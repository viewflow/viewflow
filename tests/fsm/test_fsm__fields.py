"""Tests for the django-fsm-compatible viewflow.fsm.fields.FSMField."""

from django.db import models, transaction
from django.test import TestCase

from viewflow.fsm import (
    FSMField,
    NonInitialStateOnCreate,
    NoTransition,
    TransitionConditionsUnmet,
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


class TestDeconstruct(TestCase):
    def test_deconstruct_omits_python_only_toggles(self):
        field = FSMField(
            default="new", max_length=20, protected=True, enforce_initial=True
        )
        name, path, args, kwargs = field.deconstruct()
        self.assertNotIn("protected", kwargs)
        self.assertNotIn("enforce_initial", kwargs)

    def test_deconstruct_path_is_importable(self):
        from django.utils.module_loading import import_string

        field = FSMField(default="new", max_length=20)
        name, path, args, kwargs = field.deconstruct()
        reconstructed_cls = import_string(path)
        self.assertIs(reconstructed_cls, FSMField)
