"""Model transition signals, error targets, FK storage and proxy switching."""

from django.core import serializers
from django.db import models
from django.db.migrations.state import ModelState, ProjectState
from django.forms import modelform_factory
from django.test import TestCase

from viewflow.fsm import (
    FSMField,
    FSMIntegerField,
    FSMKeyField,
    GET_STATE,
    RETURN_VALUE,
    InvalidTargetState,
    NoTransition,
    State,
    TransitionConditionsUnmet,
    transition,
)
from viewflow.fsm.signals import post_transition, pre_transition


class SignalledJob(models.Model):
    status = FSMField(default="new")
    calls = models.IntegerField(default=0)

    @transition(field=status, source="new", target="done", on_error="failed")
    def finish(self, value=None, *, fail=False):
        self.calls += 1
        if fail:
            raise ValueError("method failed")
        return self.status, value

    @transition(field=status, source="new", target="done")
    def fail(self):
        raise ValueError("no error target")

    @transition(field=status, source="new", target="done", on_error="failed")
    def interrupt(self):
        raise KeyboardInterrupt

    @transition(
        field=status,
        source="new",
        target="done",
        conditions=[lambda job: False],
        on_error="failed",
    )
    def blocked(self):
        self.calls += 1

    @transition(field=status, source="new", target=None)
    def inspect_state(self):
        return self.status

    @transition(
        field=status, source="new", target=RETURN_VALUE("done"), on_error="failed"
    )
    def dynamic(self, result):
        self.calls += 1
        return result

    @transition(
        field=status,
        source="new",
        target=GET_STATE(lambda job, result: result, states=["done"]),
        on_error="failed",
    )
    def computed(self, result):
        self.calls += 1
        return self.status


class IntegerErrorJob(models.Model):
    status = FSMIntegerField(default=1)

    @status.transition(source=1, target=2, on_error=0)
    def fail(self):
        raise ValueError("zero is a valid error state")


class RelatedState(models.Model):
    code = models.CharField(max_length=20, unique=True)


class KeyStateJob(models.Model):
    status = FSMKeyField(RelatedState, on_delete=models.PROTECT, default=1)

    @transition(field=status, source=1, target=2)
    def finish(self):
        return self.status

    @transition(field=status, source=1, target=2, on_error=3)
    def fail(self):
        raise ValueError("method failed")


class ProtectedKeyStateJob(models.Model):
    status = FSMKeyField(
        RelatedState, on_delete=models.PROTECT, default=1, protected=True
    )

    @status.transition(source=1, target=2)
    def finish(self):
        pass


class CodeStateJob(models.Model):
    status = FSMKeyField(
        RelatedState,
        to_field="code",
        on_delete=models.PROTECT,
        default="new",
        null=True,
    )

    @status.transition(source="new", target="done")
    def finish(self):
        pass


class ProxyStateJob(models.Model):
    status = FSMField(
        default="new",
        state_choices=[
            ("new", "New", "NewProxyStateJob"),
            ("done", "Done", "tests.DoneProxyStateJob"),
            ("failed", "Failed", "FailedProxyStateJob"),
        ],
    )

    @status.transition(source="new", target="done")
    def finish(self):
        return type(self)

    @status.transition(source="new", target="done", on_error="failed")
    def fail(self):
        raise ValueError("method failed")

    @status.transition(source="new", target="done")
    def abort(self):
        raise ValueError("method failed")


class NewProxyStateJob(ProxyStateJob):
    class Meta:
        proxy = True


class DoneProxyStateJob(ProxyStateJob):
    class Meta:
        proxy = True


class FailedProxyStateJob(ProxyStateJob):
    class Meta:
        proxy = True


class TestTransitionSignals(TestCase):
    def setUp(self):
        self.events = []

        def receiver(signal, **kwargs):
            self.events.append((signal, kwargs["instance"].status, kwargs))

        for signal in (pre_transition, post_transition):
            signal.connect(receiver, sender=SignalledJob, weak=False)
            self.addCleanup(signal.disconnect, receiver, sender=SignalledJob)

    def test_signal_order_payload_and_target_visible_in_method(self):
        job = SignalledJob()
        self.assertEqual(job.finish(7), ("done", 7))
        self.assertEqual(
            [(signal, state) for signal, state, _ in self.events],
            [(pre_transition, "new"), (post_transition, "done")],
        )
        for _, _, data in self.events:
            self.assertIs(data["instance"], job)
            self.assertIs(data["field"], SignalledJob._meta.get_field("status"))
            self.assertEqual(data["name"], "finish")
            self.assertEqual(data["source"], "new")
            self.assertEqual(data["target"], "done")
            self.assertEqual(data["method_args"], (7,))
            self.assertEqual(data["method_kwargs"], {})
        self.assertEqual(job.calls, 1)

    def test_on_error_changes_state_and_reports_original_exception(self):
        job = SignalledJob()
        with self.assertRaises(ValueError) as caught:
            job.finish("value", fail=True)
        self.assertEqual(job.status, "failed")
        self.assertEqual(len(self.events), 2)
        data = self.events[-1][2]
        self.assertEqual(data["target"], "failed")
        self.assertEqual(data["method_kwargs"], {"fail": True})
        self.assertIs(data["exception"], caught.exception)

    def test_no_error_target_restores_state_without_post_signal(self):
        job = SignalledJob()
        with self.assertRaises(ValueError):
            job.fail()
        self.assertEqual(job.status, "new")
        self.assertEqual([event[0] for event in self.events], [pre_transition])

    def test_validation_failure_does_not_emit_or_apply_error_target(self):
        job = SignalledJob()
        with self.assertRaises(TransitionConditionsUnmet):
            job.blocked()
        self.assertEqual(job.status, "new")
        self.assertEqual(job.calls, 0)
        job.status = "other"
        with self.assertRaises(NoTransition):
            job.finish()
        self.assertEqual(self.events, [])

    def test_no_target_reports_none_and_preserves_state(self):
        job = SignalledJob()
        self.assertEqual(job.inspect_state(), "new")
        self.assertEqual([event[2]["target"] for event in self.events], [None, None])

    def test_dynamic_targets_report_resolved_success(self):
        for method in ("dynamic", "computed"):
            with self.subTest(method=method):
                self.events.clear()
                job = SignalledJob()
                self.assertEqual(getattr(job, method)("done"), "done")
                self.assertEqual(self.events[0][1], "new")
                self.assertEqual(self.events[-1][2]["target"], "done")
                self.assertEqual(job.calls, 1)

    def test_invalid_dynamic_target_applies_error_state(self):
        for method, expected_calls in (("dynamic", 1), ("computed", 0)):
            with self.subTest(method=method):
                self.events.clear()
                job = SignalledJob()
                with self.assertRaises(InvalidTargetState) as caught:
                    getattr(job, method)("invalid")
                self.assertEqual(job.calls, expected_calls)
                self.assertEqual(job.status, "failed")
                self.assertEqual(self.events[-1][2]["target"], "failed")
                self.assertIs(self.events[-1][2]["exception"], caught.exception)

    def test_zero_integer_error_target(self):
        job = IntegerErrorJob()
        with self.assertRaises(ValueError):
            job.fail()
        self.assertEqual(job.status, 0)

    def test_interrupt_restores_state_without_error_target(self):
        job = SignalledJob()
        with self.assertRaises(KeyboardInterrupt):
            job.interrupt()
        self.assertEqual(job.status, "new")
        self.assertEqual(len(self.events), 1)

    def test_pre_receiver_failure_does_not_apply_error_target(self):
        def receiver(**kwargs):
            raise RuntimeError("receiver failed")

        pre_transition.connect(receiver, sender=SignalledJob)
        self.addCleanup(pre_transition.disconnect, receiver, sender=SignalledJob)
        job = SignalledJob()
        with self.assertRaises(RuntimeError):
            job.finish()
        self.assertEqual(job.status, "new")
        self.assertEqual(job.calls, 0)
        self.assertEqual(len(self.events), 1)

    def test_post_receiver_failure_keeps_successful_target(self):
        def receiver(**kwargs):
            raise RuntimeError("receiver failed")

        post_transition.connect(receiver, sender=SignalledJob)
        self.addCleanup(post_transition.disconnect, receiver, sender=SignalledJob)
        job = SignalledJob()
        with self.assertRaises(RuntimeError):
            job.finish()
        self.assertEqual(job.status, "done")
        self.assertEqual(job.calls, 1)
        self.assertEqual(len(self.events), 2)

    def test_plain_state_does_not_emit_model_signals(self):
        class Flow:
            status = State(states=None, default="new")

            @status.transition(source="new", target="done")
            def finish(self):
                pass

        def receiver(**kwargs):
            self.fail("plain State should not emit model-field signals")

        for signal in (pre_transition, post_transition):
            signal.connect(receiver, sender=Flow)
            self.addCleanup(signal.disconnect, receiver, sender=Flow)
        Flow().finish()


class TestKeyStateFields(TestCase):
    @classmethod
    def setUpTestData(cls):
        for pk, code in ((1, "new"), (2, "done"), (3, "failed")):
            RelatedState.objects.create(pk=pk, code=code)

    def test_foreign_key_round_trip_and_lookup(self):
        job = KeyStateJob.objects.create()
        self.assertEqual(job.status, 1)
        self.assertEqual(job.status_id, 1)
        self.assertEqual(job.finish(), 2)
        job.save()
        reloaded = KeyStateJob.objects.get(pk=job.pk)
        self.assertEqual(reloaded.status, 2)
        self.assertEqual(KeyStateJob.objects.get(status__code="done").pk, job.pk)

    def test_deferred_state_loads_key_for_transition(self):
        job = KeyStateJob.objects.create()
        deferred = KeyStateJob.objects.only("pk").get(pk=job.pk)
        with self.assertNumQueries(1):
            self.assertEqual(deferred.status, 1)
        deferred.finish()
        deferred.save(update_fields=["status"])
        self.assertEqual(KeyStateJob.objects.get(pk=job.pk).status_id, 2)

    def test_both_attribute_names_respect_protection(self):
        job = ProtectedKeyStateJob.objects.create()
        for name in ("status", "status_id"):
            with self.subTest(name=name), self.assertRaises(AttributeError):
                setattr(job, name, 2)
        job.finish()
        job.save()
        self.assertEqual(ProtectedKeyStateJob.objects.get(pk=job.pk).status, 2)

    def test_on_error_stores_error_key(self):
        job = KeyStateJob.objects.create()
        with self.assertRaises(ValueError):
            job.fail()
        job.save()
        self.assertEqual(KeyStateJob.objects.get(pk=job.pk).status, 3)

    def test_select_related_can_be_saved(self):
        job = KeyStateJob.objects.create()
        loaded = KeyStateJob.objects.select_related("status").get(pk=job.pk)
        self.assertEqual(loaded.status, 1)
        loaded.finish()
        loaded.save()
        self.assertEqual(KeyStateJob.objects.get(pk=job.pk).status, 2)

    def test_model_form_assigns_state_key(self):
        form_class = modelform_factory(KeyStateJob, fields=["status"])
        form = form_class(data={"status": "2"})
        self.assertTrue(form.is_valid(), form.errors)
        job = form.save()
        self.assertEqual(job.status, 2)
        self.assertEqual(KeyStateJob.objects.get(pk=job.pk).status, 2)

    def test_to_field_nullable_and_serialization(self):
        job = CodeStateJob.objects.create()
        job.finish()
        job.save()
        self.assertEqual(CodeStateJob.objects.get(pk=job.pk).status, "done")
        payload = serializers.serialize("json", [job])
        restored = next(serializers.deserialize("json", payload)).object
        self.assertEqual(restored.status, "done")
        restored.status = None
        restored.save()
        self.assertIsNone(CodeStateJob.objects.get(pk=job.pk).status)

    def test_unsaved_related_state_is_rejected(self):
        with self.assertRaises(ValueError):
            KeyStateJob(status=RelatedState(code="unsaved"))

    def test_clone_preserves_relation_and_protection(self):
        field = ProtectedKeyStateJob._meta.get_field("status")
        cloned = field.clone()
        self.assertIsInstance(cloned, FSMKeyField)
        self.assertTrue(cloned.protected)
        self.assertEqual(cloned.remote_field.model, "tests.relatedstate")

    def test_historical_model_reconstructs_key_storage(self):
        state = ProjectState()
        for model in (RelatedState, KeyStateJob):
            state.add_model(ModelState.from_model(model))
        historical = state.apps.get_model("tests", "KeyStateJob")
        job = historical()
        self.assertEqual(job.status, 1)
        job.status = 2
        self.assertEqual(job.status_id, 2)


class TestProxyStateFields(TestCase):
    def test_default_loading_and_transition_switch_classes(self):
        job = ProxyStateJob.objects.create()
        self.assertIs(type(job), NewProxyStateJob)
        self.assertIs(job.finish(), DoneProxyStateJob)
        job.save()
        self.assertIs(type(ProxyStateJob.objects.get(pk=job.pk)), DoneProxyStateJob)

    def test_direct_assignment_switches_proxy(self):
        job = ProxyStateJob()
        job.status = "done"
        self.assertIs(type(job), DoneProxyStateJob)

    def test_deferred_state_selects_proxy_when_loaded(self):
        job = ProxyStateJob.objects.create(status="done")
        deferred = ProxyStateJob.objects.only("pk").get(pk=job.pk)
        self.assertIs(type(deferred), ProxyStateJob)
        self.assertEqual(deferred.status, "done")
        self.assertIs(type(deferred), DoneProxyStateJob)

    def test_abort_restores_source_proxy(self):
        job = ProxyStateJob()
        with self.assertRaises(ValueError):
            job.abort()
        self.assertEqual(job.status, "new")
        self.assertIs(type(job), NewProxyStateJob)

    def test_error_target_selects_error_proxy(self):
        job = ProxyStateJob()
        with self.assertRaises(ValueError):
            job.fail()
        self.assertEqual(job.status, "failed")
        self.assertIs(type(job), FailedProxyStateJob)

    def test_signal_sender_stays_source_proxy(self):
        events = []

        def receiver(signal, sender, **kwargs):
            events.append((signal, sender, type(kwargs["instance"])))

        for signal in (pre_transition, post_transition):
            signal.connect(receiver, sender=NewProxyStateJob)
            self.addCleanup(signal.disconnect, receiver, sender=NewProxyStateJob)
        job = ProxyStateJob()
        job.finish()
        self.assertEqual(
            events,
            [
                (pre_transition, NewProxyStateJob, NewProxyStateJob),
                (post_transition, NewProxyStateJob, DoneProxyStateJob),
            ],
        )

    def test_deferred_transition_signals_use_loaded_source_proxy(self):
        events = []

        def receiver(sender, **kwargs):
            events.append(sender)

        pre_transition.connect(receiver, sender=NewProxyStateJob)
        self.addCleanup(pre_transition.disconnect, receiver, sender=NewProxyStateJob)
        job = ProxyStateJob.objects.create()
        deferred = ProxyStateJob.objects.only("pk").get(pk=job.pk)
        deferred.finish()
        self.assertEqual(events, [NewProxyStateJob])
        self.assertIs(type(deferred), DoneProxyStateJob)

    def test_choices_and_clone_preserve_proxy_mapping(self):
        field = ProxyStateJob._meta.get_field("status")
        self.assertEqual(
            list(field.choices),
            [("new", "New"), ("done", "Done"), ("failed", "Failed")],
        )
        cloned = field.clone()
        self.assertEqual(cloned.state_choices, field.state_choices)
        self.assertEqual(cloned.state_proxy, field.state_proxy)
        job = ProxyStateJob()
        self.assertEqual(job.get_status_display(), "New")

    def test_historical_models_use_historical_proxy_registry(self):
        state = ProjectState()
        for model in (
            ProxyStateJob,
            NewProxyStateJob,
            DoneProxyStateJob,
            FailedProxyStateJob,
        ):
            state.add_model(ModelState.from_model(model))
        historical = state.apps.get_model("tests", "ProxyStateJob")
        job = historical()
        self.assertIs(type(job), state.apps.get_model("tests", "NewProxyStateJob"))
        job.status = "done"
        self.assertIs(type(job), state.apps.get_model("tests", "DoneProxyStateJob"))

    def test_choices_and_state_choices_are_mutually_exclusive(self):
        with self.assertRaises(ValueError):
            FSMField(
                choices=[("new", "New")],
                state_choices=[("new", "New", "NewProxyStateJob")],
            )

    def test_unrelated_proxy_mapping_is_rejected_without_writing_state(self):
        field = FSMField(state_choices=[("new", "New", "DoneProxyStateJob")])
        field.set_attributes_from_name("status")
        field.model = SignalledJob
        job = SignalledJob()
        with self.assertRaises(ValueError):
            field.set_state(job, "new")
        self.assertIs(type(job), SignalledJob)
        self.assertEqual(job.status, "new")
