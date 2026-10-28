"""Tests for the django-fsm-compatible viewflow.fsm.fields.FSMField."""

from django.db import models, transaction
from django.db.migrations.state import ModelState
from django.test import TestCase

from viewflow.fsm import (
    FSMField,
    NonInitialStateOnCreate,
    NoTransition,
    TransitionConditionsUnmet,
    State,
    can_proceed,
    has_transition_perm,
    transition,
)


class Job(models.Model):
    status = FSMField(default="new", max_length=20)

    @status.transition(source="new", target="running")
    def start(self):
        pass

    @status.transition(source="running", target="done")
    def finish(self):
        pass


class TestBasicRoundTrip(TestCase):
    def test_new_instance_starts_at_default(self):
        job = Job()
        self.assertEqual(job.status, "new")

    def test_transition_changes_in_memory_state(self):
        job = Job.objects.create()
        job.start()
        self.assertEqual(job.status, "running")

    def test_transition_persists_across_save_and_reload(self):
        job = Job.objects.create()
        job.start()
        job.save()

        reloaded = Job.objects.get(pk=job.pk)
        self.assertEqual(reloaded.status, "running")

    def test_second_transition_after_reload(self):
        job = Job.objects.create()
        job.start()
        job.save()

        reloaded = Job.objects.get(pk=job.pk)
        reloaded.finish()
        reloaded.save()

        self.assertEqual(Job.objects.get(pk=job.pk).status, "done")

    def test_queryset_filter_by_field_value(self):
        Job.objects.create()
        running = Job.objects.create()
        running.start()
        running.save()

        self.assertEqual(Job.objects.filter(status="running").get().pk, running.pk)

    def test_invalid_transition_raises(self):
        job = Job.objects.create()
        with self.assertRaises(NoTransition):
            job.finish()  # not running yet

    def test_meta_get_field_returns_the_field_object(self):
        field = Job._meta.get_field("status")
        self.assertIsInstance(field, FSMField)

    def test_deferred_state_loads_database_value(self):
        job = Job.objects.create(status="running")
        for queryset in (Job.objects.only("pk"), Job.objects.defer("status")):
            with self.subTest(queryset=queryset):
                deferred = queryset.get(pk=job.pk)
                self.assertIn("status", deferred.get_deferred_fields())
                with self.assertNumQueries(1):
                    self.assertEqual(deferred.status, "running")
                with self.assertNumQueries(0):
                    self.assertEqual(deferred.status, "running")

    def test_transition_uses_deferred_database_state(self):
        job = Job.objects.create(status="running")
        deferred = Job.objects.only("pk").get(pk=job.pk)
        deferred.finish()
        deferred.save(update_fields=["status"])
        self.assertEqual(Job.objects.get(pk=job.pk).status, "done")


class JobWithCondition(models.Model):
    status = FSMField(default="new", max_length=20)
    ready = models.BooleanField(default=False)

    @status.transition(
        source="new", target="running", conditions=[lambda job: job.ready]
    )
    def start(self):
        pass


class TestConditions(TestCase):
    def test_unmet_condition_blocks_transition(self):
        job = JobWithCondition.objects.create(ready=False)
        with self.assertRaises(TransitionConditionsUnmet):
            job.start()

    def test_met_condition_allows_transition(self):
        job = JobWithCondition.objects.create(ready=True)
        job.start()
        self.assertEqual(job.status, "running")


class ProtectedJob(models.Model):
    status = FSMField(default="new", max_length=20, protected=True)

    @status.transition(source="new", target="running")
    def start(self):
        pass


class TestProtected(TestCase):
    def test_direct_assignment_after_construction_raises(self):
        job = ProtectedJob.objects.create()
        with self.assertRaises(AttributeError):
            job.status = "running"

    def test_transition_still_works(self):
        job = ProtectedJob.objects.create()
        job.start()
        self.assertEqual(job.status, "running")

    def test_construction_with_explicit_value_is_the_allowed_first_write(self):
        # Matches django-fsm: protected blocks *subsequent* direct writes,
        # not the very first one Django itself performs during __init__.
        job = ProtectedJob(status="running")
        self.assertEqual(job.status, "running")

    def test_refresh_from_db_is_a_known_limitation(self):
        # Documented limitation: refresh_from_db() re-assigns the field via
        # the same protected __set__, and the slot is already populated by
        # then, so it raises exactly like any other direct assignment would.
        job = ProtectedJob.objects.create()
        with self.assertRaises(AttributeError):
            job.refresh_from_db()

    def test_deferred_protected_state_can_load_and_transition(self):
        job = ProtectedJob.objects.create()
        deferred = ProtectedJob.objects.only("pk").get(pk=job.pk)
        self.assertEqual(deferred.status, "new")
        with self.assertRaises(AttributeError):
            deferred.status = "running"
        deferred.start()
        deferred.save()
        self.assertEqual(ProtectedJob.objects.get(pk=job.pk).status, "running")


class UnprotectedJob(models.Model):
    status = FSMField(default="new", max_length=20)

    @status.transition(source="new", target="running")
    def start(self):
        pass


class TestUnprotectedDefault(TestCase):
    def test_direct_assignment_allowed_by_default(self):
        # protected=False (the default) matches django-fsm's own default --
        # a same-behavior import swap, not an automatic tightening.
        job = UnprotectedJob.objects.create()
        job.status = "running"
        self.assertEqual(job.status, "running")

    def test_refresh_from_db_works_when_unprotected(self):
        job = UnprotectedJob.objects.create()
        job.refresh_from_db()
        self.assertEqual(job.status, "new")


class EnforcedJob(models.Model):
    status = FSMField(default="new", max_length=20, enforce_initial=True)

    @status.transition(source="new", target="running")
    def start(self):
        pass


class TestEnforceInitial(TestCase):
    def test_create_at_default_succeeds(self):
        job = EnforcedJob.objects.create()
        self.assertEqual(job.status, "new")

    def test_create_at_non_default_raises(self):
        with self.assertRaises(NonInitialStateOnCreate):
            EnforcedJob.objects.create(status="running")

    def test_create_at_non_default_does_not_insert_a_row(self):
        with transaction.atomic():
            with self.assertRaises(NonInitialStateOnCreate):
                EnforcedJob.objects.create(status="running")
        self.assertEqual(EnforcedJob.objects.count(), 0)

    def test_update_after_creation_is_not_checked(self):
        # enforce_initial only guards `add` (INSERT); a legitimate
        # transition-driven save is an UPDATE and is untouched.
        job = EnforcedJob.objects.create()
        job.start()
        job.save()
        self.assertEqual(EnforcedJob.objects.get(pk=job.pk).status, "running")

    def test_bulk_create_at_non_default_raises(self):
        with transaction.atomic():
            with self.assertRaises(NonInitialStateOnCreate):
                EnforcedJob.objects.bulk_create([EnforcedJob(status="running")])
        self.assertEqual(EnforcedJob.objects.count(), 0)


class NoEnforcementByDefault(models.Model):
    status = FSMField(default="new", max_length=20)

    @status.transition(source="new", target="running")
    def start(self):
        pass


class TestEnforceInitialDefaultOff(TestCase):
    def test_create_at_non_default_succeeds_by_default(self):
        # enforce_initial=False (the default) matches django-fsm: ported
        # code that relied on unrestricted creation keeps working.
        job = NoEnforcementByDefault.objects.create(status="running")
        self.assertEqual(job.status, "running")


class LegacyStyleJob(models.Model):
    status = FSMField(default="new", max_length=20)

    @transition(field=status, source="new", target="running")
    def start(self):
        pass


class TestDjangoFsmCompatDecorator(TestCase):
    def test_field_kwarg_style_decorator_works(self):
        job = LegacyStyleJob.objects.create()
        job.start()
        job.save()
        self.assertEqual(LegacyStyleJob.objects.get(pk=job.pk).status, "running")

    def test_default_source_and_permissions(self):
        field = LegacyStyleJob._meta.get_field("status")

        @transition(field=field, target="done")
        def finish(job):
            return job.status

        job = LegacyStyleJob(status="running")
        bound = finish.__get__(job, LegacyStyleJob)
        self.assertTrue(bound.has_perm(None))
        # Like native State transitions, the method sees its target state.
        self.assertEqual(bound(), "done")
        self.assertEqual(job.status, "done")

    def test_wildcard_and_none_target(self):
        field = LegacyStyleJob._meta.get_field("status")

        @transition(field=field, source="*", target=None)
        def check(job):
            return job.status

        job = LegacyStyleJob(status="running")
        self.assertEqual(check.__get__(job, LegacyStyleJob)(), "running")
        self.assertEqual(job.status, "running")

    def test_wildcard_in_source_collection(self):
        field = LegacyStyleJob._meta.get_field("status")

        @transition(field=field, source=["new", "*"], target="done")
        def finish(job):
            pass

        job = LegacyStyleJob(status="running")
        finish.__get__(job, LegacyStyleJob)()
        self.assertEqual(job.status, "done")

    def test_native_state_api_still_rejects_none_target(self):
        state = State(states=None)
        with self.assertRaises(ValueError):
            state.transition(source=State.ANY, target=None)

    def test_can_proceed_checks_state(self):
        job = LegacyStyleJob()
        self.assertTrue(can_proceed(job.start))
        self.assertTrue(has_transition_perm(job.start, None))
        job.start()
        self.assertFalse(can_proceed(job.start))
        self.assertFalse(has_transition_perm(job.start, None))

    def test_can_proceed_can_skip_conditions(self):
        job = JobWithCondition(ready=False)
        self.assertFalse(can_proceed(job.start))
        self.assertTrue(can_proceed(job.start, check_conditions=False))
        job.status = "done"
        self.assertFalse(can_proceed(job.start, check_conditions=False))

    def test_permission_helper_checks_conditions_and_permission(self):
        field = LegacyStyleJob._meta.get_field("status")

        @transition(
            field=field,
            source="new",
            target="done",
            conditions=[lambda job: job.pk is not None],
            permission=lambda job, user: user == "editor",
        )
        def finish(job):
            pass

        job = LegacyStyleJob()
        bound = finish.__get__(job, LegacyStyleJob)
        self.assertFalse(has_transition_perm(bound, "editor"))
        job.save()
        self.assertFalse(has_transition_perm(bound, "reader"))
        self.assertTrue(has_transition_perm(bound, "editor"))
        bound()
        self.assertFalse(has_transition_perm(bound, "editor"))


class TestDeconstruct(TestCase):
    def test_deconstruct_preserves_options(self):
        field = FSMField(
            default="new", max_length=20, protected=True, enforce_initial=True
        )
        name, path, args, kwargs = field.deconstruct()
        restored = FSMField(*args, **kwargs)
        self.assertTrue(restored.protected)
        self.assertTrue(restored.enforce_initial)

    def test_default_options_do_not_add_migration_arguments(self):
        _, _, _, kwargs = FSMField(max_length=20).deconstruct()
        self.assertNotIn("protected", kwargs)
        self.assertNotIn("enforce_initial", kwargs)

    def test_migration_state_preserves_protection(self):
        state = ModelState.from_model(ProtectedJob)
        self.assertTrue(state.fields["status"].protected)

    def test_cloned_field_uses_its_own_storage_name(self):
        import copy

        original = Job._meta.get_field("status")
        cloned = copy.deepcopy(original)
        cloned.name = "other_status"
        cloned.set_attributes_from_name("other_status")
        job = Job(status="new")
        cloned.__set__(job, "done")
        self.assertEqual(cloned.__get__(job, Job), "done")
        self.assertEqual(job.status, "new")

    def test_deconstruct_path_is_importable(self):
        from django.utils.module_loading import import_string

        field = FSMField(default="new", max_length=20)
        name, path, args, kwargs = field.deconstruct()
        reconstructed_cls = import_string(path)
        self.assertIs(reconstructed_cls, FSMField)
