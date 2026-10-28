"""Regression coverage for the supported django-fsm model API."""

from django.contrib.auth.models import Permission, User
from django.core import serializers
from django.db import models
from django.test import TestCase
from guardian.shortcuts import assign_perm

from viewflow.fsm import (
    FSMField,
    FSMIntegerField,
    FSMModelMixin,
    GET_STATE,
    RETURN_VALUE,
    InvalidTargetState,
    NoTransition,
    can_proceed,
    has_transition_perm,
    transition,
)


class LegacyWorkflowMixin:
    @transition(
        field="status",
        source="new",
        target="running",
        conditions=[lambda job: job.ready],
        permission="tests.start_job",
        custom={"label": "Start"},
    )
    def start(self):
        return self.status

    @transition(field="status", source="running", target="done")
    @transition(field="status", source="new", target="done")
    def finish(self):
        self.calls += 1

    @transition(field="status", source="+", target="removed")
    def remove(self):
        pass


class AbstractLegacyJob(FSMModelMixin, models.Model):
    status = FSMField(default="new", protected=True)
    ready = models.BooleanField(default=False)
    calls = models.IntegerField(default=0)

    class Meta:
        abstract = True


class LegacyCompatJob(LegacyWorkflowMixin, AbstractLegacyJob):
    phase = FSMIntegerField(default=0, protected=True)

    @phase.transition(source=0, target=1)
    def advance(self):
        pass

    class Meta:
        permissions = [("start_job", "Can start job")]


class OtherLegacyCompatJob(LegacyWorkflowMixin, AbstractLegacyJob):
    pass


class DynamicLegacyJob(models.Model):
    status = FSMField(default="new")

    @transition(field=status, source="new", target=RETURN_VALUE("running", "done"))
    def start(self, result):
        return result

    @transition(
        field=status,
        source="running",
        target=GET_STATE(
            lambda job, allowed: "done" if allowed else "rejected",
            states=["done", "rejected"],
        ),
    )
    def moderate(self, allowed):
        return self.status


class TestLegacyFieldAPI(TestCase):
    def test_default_char_length_matches_django_fsm(self):
        self.assertEqual(FSMField().max_length, 50)
        self.assertEqual(FSMField(max_length=100).max_length, 100)

    def test_string_field_mixin_and_stacked_transitions(self):
        job = LegacyCompatJob.objects.create(ready=True)
        self.assertEqual(job.start(), "running")
        job.finish()
        self.assertEqual(job.calls, 1)
        job.save()
        self.assertEqual(LegacyCompatJob.objects.get(pk=job.pk).status, "done")

    def test_abstract_fields_bind_to_each_concrete_model(self):
        for cls in (LegacyCompatJob, OtherLegacyCompatJob):
            with self.subTest(model=cls):
                job = cls.objects.create(ready=True)
                bound_field = job.start._state._field
                self.assertIs(bound_field, cls._meta.get_field("status"))
                job.start()
                job.save()
                self.assertEqual(cls.objects.get(pk=job.pk).status, "running")

    def test_discovery_separates_fields_and_retains_metadata(self):
        job = LegacyCompatJob(ready=True)
        transitions = list(job.get_all_status_transitions())
        self.assertEqual(len(transitions), 4)
        start = next(item for item in transitions if item.name == "start")
        self.assertEqual(start.custom, {"label": "Start"})
        self.assertEqual(start.method.__name__, "start")
        self.assertEqual(start.target, "running")
        self.assertEqual(
            [item.name for item in job.get_all_phase_transitions()], ["advance"]
        )

    def test_available_transitions_check_conditions_and_source(self):
        job = LegacyCompatJob()
        self.assertEqual(
            {t.name for t in job.get_available_status_transitions()},
            {"finish", "remove"},
        )
        job.ready = True
        self.assertEqual(
            {t.name for t in job.get_available_status_transitions()},
            {"start", "finish", "remove"},
        )
        job.finish()
        self.assertEqual(
            [t.name for t in job.get_available_status_transitions()], ["remove"]
        )

    def test_plus_disallows_reentering_target(self):
        job = LegacyCompatJob()
        self.assertTrue(can_proceed(job.remove))
        job.remove()
        self.assertFalse(can_proceed(job.remove))
        self.assertEqual(list(job.get_available_status_transitions()), [])
        with self.assertRaises(NoTransition):
            job.remove()

    def test_explicit_source_takes_precedence_over_plus(self):
        field = LegacyCompatJob._meta.get_field("status")

        @transition(field=field, source="new", target="running")
        @transition(field=field, source="+", target="done")
        def move(job):
            pass

        job = LegacyCompatJob()
        bound = move.__get__(job, LegacyCompatJob)
        bound()
        self.assertEqual(job.status, "running")
        bound()
        self.assertEqual(job.status, "done")
        self.assertFalse(can_proceed(bound))

    def test_stacked_transitions_reject_different_unbound_fields(self):
        first, second = FSMField(), FSMField()
        with self.assertRaises(ValueError):

            @transition(field=first, source="new", target="running")
            @transition(field=second, source="new", target="done")
            def move(job):
                pass

    def test_global_string_permission(self):
        user = User.objects.create_user(username="global")
        user.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="tests", codename="start_job"
            )
        )
        job = LegacyCompatJob.objects.create(ready=True)
        self.assertTrue(has_transition_perm(job.start, user))
        self.assertEqual(
            {t.name for t in job.get_available_user_status_transitions(user)},
            {"start", "finish", "remove"},
        )

    def test_object_string_permission(self):
        user = User.objects.create_user(username="object")
        job = LegacyCompatJob.objects.create(ready=True)
        assign_perm("tests.start_job", user, job)
        self.assertTrue(has_transition_perm(job.start, user))
        other = LegacyCompatJob.objects.create(ready=True)
        self.assertFalse(has_transition_perm(other.start, user))

    def test_missing_permission_and_unmet_conditions(self):
        user = User.objects.create_user(username="unprivileged")
        job = LegacyCompatJob(ready=True)
        self.assertFalse(has_transition_perm(job.start, user))
        self.assertEqual(
            {t.name for t in job.get_available_user_status_transitions(user)},
            {"finish", "remove"},
        )

    def test_integer_field_round_trip_and_protection(self):
        job = LegacyCompatJob.objects.create()
        job.advance()
        job.save(update_fields=["phase"])
        reloaded = LegacyCompatJob.objects.only("pk").get(pk=job.pk)
        self.assertEqual(reloaded.phase, 1)
        self.assertFalse(can_proceed(reloaded.advance))
        with self.assertRaises(AttributeError):
            reloaded.phase = 0
        serialized = serializers.serialize("json", [job])
        restored = next(serializers.deserialize("json", serialized)).object
        self.assertEqual(restored.phase, 1)

    def test_integer_field_clone_preserves_options(self):
        field = FSMIntegerField(default=0, protected=True, enforce_initial=True)
        cloned = field.clone()
        self.assertIsInstance(cloned, FSMIntegerField)
        self.assertTrue(cloned.protected)
        self.assertTrue(cloned.enforce_initial)
        self.assertEqual(cloned.get_default(), 0)

    def test_refresh_mixin_skips_protected_fields(self):
        job = LegacyCompatJob.objects.create()
        LegacyCompatJob.objects.filter(pk=job.pk).update(
            ready=True, status="running", phase=1
        )
        job.refresh_from_db()
        self.assertTrue(job.ready)
        self.assertEqual(job.status, "new")
        self.assertEqual(job.phase, 0)

    def test_refresh_mixin_honors_explicit_fields(self):
        job = LegacyCompatJob.objects.create()
        LegacyCompatJob.objects.filter(pk=job.pk).update(ready=True)
        job.refresh_from_db(fields=["ready"])
        self.assertTrue(job.ready)
        with self.assertRaises(AttributeError):
            job.refresh_from_db(fields=["status"])

    def test_dynamic_target_exports(self):
        job = DynamicLegacyJob.objects.create()
        job.start("running")
        self.assertEqual(job.moderate(allowed=False), "rejected")
        job.save()
        self.assertEqual(DynamicLegacyJob.objects.get(pk=job.pk).status, "rejected")

    def test_invalid_return_value_is_rejected(self):
        job = DynamicLegacyJob()
        with self.assertRaises(InvalidTargetState):
            job.start("invalid")
        self.assertEqual(job.status, "new")
