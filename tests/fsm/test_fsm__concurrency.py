"""Optimistic state checks on ordinary and partial model saves."""

from django.db import DatabaseError, models, transaction
from django.test import TestCase

from viewflow.fsm import (
    ConcurrentTransition,
    ConcurrentTransitionMixin,
    FSMField,
    FSMIntegerField,
    FSMKeyField,
    FSMModelMixin,
)


class ConcurrentJob(ConcurrentTransitionMixin, models.Model):
    status = FSMField(default="new")
    phase = FSMIntegerField(default=0)
    text = models.CharField(max_length=50, default="")

    @status.transition(source="new", target="running")
    def start(self):
        pass

    @status.transition(source="running", target="done")
    def finish(self):
        pass

    @phase.transition(source=0, target=1)
    def advance(self):
        pass


class ConcurrentChildJob(ConcurrentJob):
    review = FSMField(default="waiting", protected=True)
    notes = models.CharField(max_length=50, default="")

    @review.transition(source="waiting", target="rejected")
    def reject(self):
        pass


class ProtectedConcurrentBase(models.Model):
    status = FSMField(default="new", protected=True)
    text = models.CharField(max_length=50, default="")

    @status.transition(source="new", target="running")
    def start(self):
        pass

    class Meta:
        abstract = True


class ProtectedConcurrentJob(
    FSMModelMixin, ConcurrentTransitionMixin, ProtectedConcurrentBase
):
    pass


class ReversedProtectedConcurrentJob(
    ConcurrentTransitionMixin, FSMModelMixin, ProtectedConcurrentBase
):
    pass


class NullableConcurrentJob(ConcurrentTransitionMixin, models.Model):
    status = FSMIntegerField(null=True, default=None)

    @status.transition(source=None, target=0)
    def start(self):
        pass


class ConcurrencyState(models.Model):
    code = models.CharField(max_length=20, primary_key=True)


class KeyConcurrentJob(ConcurrentTransitionMixin, models.Model):
    status = FSMKeyField(ConcurrencyState, on_delete=models.PROTECT, default="new")

    @status.transition(source="new", target="done")
    def finish(self):
        pass


class ProxyConcurrentJob(ConcurrentTransitionMixin, models.Model):
    status = FSMField(
        default="new",
        state_choices=[
            ("new", "New", "NewConcurrentJob"),
            ("running", "Running", "RunningConcurrentJob"),
        ],
    )

    @status.transition(source="new", target="running")
    def start(self):
        pass


class NewConcurrentJob(ProxyConcurrentJob):
    class Meta:
        proxy = True


class RunningConcurrentJob(ProxyConcurrentJob):
    class Meta:
        proxy = True


class ConcurrentTransitionTests(TestCase):
    def test_successful_saves_advance_baseline(self):
        job = ConcurrentJob.objects.create()
        job.start()
        job.save()
        job.finish()
        job.save()
        self.assertEqual(ConcurrentJob.objects.get(pk=job.pk).status, "done")

    def test_stale_transition_cannot_overwrite_winner(self):
        first = ConcurrentJob.objects.create()
        stale = ConcurrentJob.objects.get(pk=first.pk)
        first.start()
        first.save()
        stale.start()
        stale.text = "stale"
        with self.assertRaises(ConcurrentTransition), transaction.atomic():
            stale.save()
        winner = ConcurrentJob.objects.get(pk=first.pk)
        self.assertEqual(winner.status, "running")
        self.assertEqual(winner.text, "")

    def test_non_state_update_checks_observed_state(self):
        first = ConcurrentJob.objects.create()
        stale = ConcurrentJob.objects.get(pk=first.pk)
        first.start()
        first.save()
        stale.text = "stale"
        with self.assertRaises(ConcurrentTransition), transaction.atomic():
            stale.save(update_fields=["text"])

    def test_all_state_columns_participate_in_check(self):
        first = ConcurrentJob.objects.create()
        stale = ConcurrentJob.objects.get(pk=first.pk)
        first.advance()
        first.save(update_fields=["phase"])
        stale.start()
        with self.assertRaises(ConcurrentTransition), transaction.atomic():
            stale.save(update_fields=["status"])

    def test_partial_save_does_not_accept_unsaved_state_changes(self):
        job = ConcurrentJob.objects.create()
        job.start()
        job.advance()
        job.text = "changed"
        job.save(update_fields=["text"])
        stored = ConcurrentJob.objects.get(pk=job.pk)
        self.assertEqual((stored.status, stored.phase), ("new", 0))
        job.save(update_fields=["status"])
        job.save(update_fields=["phase"])
        stored = ConcurrentJob.objects.get(pk=job.pk)
        self.assertEqual((stored.status, stored.phase), ("running", 1))

    def test_empty_update_fields_does_not_advance_baseline(self):
        job = ConcurrentJob.objects.create()
        job.start()
        job.save(update_fields=[])
        self.assertEqual(ConcurrentJob.objects.get(pk=job.pk).status, "new")
        job.save(update_fields=["status"])
        self.assertEqual(ConcurrentJob.objects.get(pk=job.pk).status, "running")

    def test_update_fields_accepts_generator(self):
        job = ConcurrentJob.objects.create()
        job.start()
        job.save(update_fields=(name for name in ["status"]))
        job.finish()
        job.save(update_fields=["status"])
        self.assertEqual(ConcurrentJob.objects.get(pk=job.pk).status, "done")

    def test_refresh_allows_further_transition(self):
        first = ConcurrentJob.objects.create()
        stale = ConcurrentJob.objects.get(pk=first.pk)
        first.start()
        first.save()
        stale.refresh_from_db()
        stale.finish()
        stale.save()
        self.assertEqual(ConcurrentJob.objects.get(pk=first.pk).status, "done")

    def test_partial_refresh_preserves_dirty_state_baseline(self):
        job = ConcurrentJob.objects.create()
        job.start()
        job.refresh_from_db(fields=["text"])
        job.save(update_fields=["status"])
        self.assertEqual(ConcurrentJob.objects.get(pk=job.pk).status, "running")

    def test_partial_refresh_cannot_hide_conflict(self):
        first = ConcurrentJob.objects.create()
        stale = ConcurrentJob.objects.get(pk=first.pk)
        first.start()
        first.save()
        stale.start()
        stale.refresh_from_db(fields=["text"])
        with self.assertRaises(ConcurrentTransition), transaction.atomic():
            stale.save(update_fields=["status"])

    def test_deferred_construction_does_not_fetch_state_columns(self):
        job = ConcurrentJob.objects.create()
        with self.assertNumQueries(1):
            deferred = ConcurrentJob.objects.only("pk", "text").get(pk=job.pk)
        self.assertIn("status", deferred.get_deferred_fields())
        self.assertIn("phase", deferred.get_deferred_fields())

    def test_deferred_read_records_state_for_conflict_check(self):
        first = ConcurrentJob.objects.create()
        stale = ConcurrentJob.objects.only("pk", "text").get(pk=first.pk)
        with self.assertNumQueries(1):
            self.assertEqual(stale.status, "new")
        first.start()
        first.save()
        stale.start()
        with self.assertRaises(ConcurrentTransition), transaction.atomic():
            stale.save(update_fields=["status"])

    def test_save_unobserved_deferred_states_uses_current_database_baseline(self):
        first = ConcurrentJob.objects.create()
        deferred = ConcurrentJob.objects.only("pk", "text").get(pk=first.pk)
        first.start()
        first.save()
        deferred.text = "new text"
        deferred.save(update_fields=["text"])
        stored = ConcurrentJob.objects.get(pk=first.pk)
        self.assertEqual(stored.status, "running")
        self.assertEqual(stored.text, "new text")
        self.assertIn("status", deferred.get_deferred_fields())

    def test_direct_assignment_of_unobserved_deferred_state(self):
        job = ConcurrentJob.objects.create()
        deferred = ConcurrentJob.objects.only("pk").get(pk=job.pk)
        deferred.status = "running"
        deferred.save(update_fields=["status"])
        self.assertEqual(ConcurrentJob.objects.get(pk=job.pk).status, "running")

    def test_insert_with_explicit_primary_key_is_not_a_conflict(self):
        job = ConcurrentJob(pk=300, status="running")
        job.save()
        self.assertEqual(ConcurrentJob.objects.get(pk=300).status, "running")

    def test_deleted_row_force_update_raises_database_error(self):
        job = ConcurrentJob.objects.create()
        ConcurrentJob.objects.filter(pk=job.pk).delete()
        with self.assertRaises(DatabaseError):
            job.save(force_update=True)

    def test_inherited_parent_and_child_states(self):
        first = ConcurrentChildJob.objects.create()
        stale = ConcurrentChildJob.objects.get(pk=first.pk)
        first.reject()
        first.save()
        stale.text = "must roll back with the child conflict"
        with self.assertRaises(ConcurrentTransition), transaction.atomic():
            stale.save()
        self.assertEqual(ConcurrentChildJob.objects.get(pk=first.pk).text, "")
        first.start()
        first.save()
        self.assertEqual(ConcurrentChildJob.objects.get(pk=first.pk).status, "running")

    def test_protected_refresh_mixins_preserve_baseline_in_both_orders(self):
        for cls in (ProtectedConcurrentJob, ReversedProtectedConcurrentJob):
            with self.subTest(model=cls):
                first = cls.objects.create()
                stale = cls.objects.get(pk=first.pk)
                first.start()
                first.save()
                stale.start()
                stale.refresh_from_db()
                with self.assertRaises(ConcurrentTransition), transaction.atomic():
                    stale.save()
                fresh = cls.objects.get(pk=first.pk)
                fresh.text = "updated"
                fresh.refresh_from_db()
                fresh.save()

    def test_null_and_zero_states(self):
        first = NullableConcurrentJob.objects.create()
        stale = NullableConcurrentJob.objects.get(pk=first.pk)
        first.start()
        first.save()
        stale.start()
        with self.assertRaises(ConcurrentTransition), transaction.atomic():
            stale.save()

    def test_foreign_key_states(self):
        for code in ("new", "done"):
            ConcurrencyState.objects.create(code=code)
        first = KeyConcurrentJob.objects.create()
        stale = KeyConcurrentJob.objects.get(pk=first.pk)
        first.finish()
        first.save()
        stale.finish()
        with self.assertRaises(ConcurrentTransition), transaction.atomic():
            stale.save()

    def test_proxy_switch_keeps_snapshot(self):
        first = ProxyConcurrentJob.objects.create()
        stale = ProxyConcurrentJob.objects.get(pk=first.pk)
        first.start()
        first.save()
        stale.start()
        self.assertIs(type(stale), RunningConcurrentJob)
        with self.assertRaises(ConcurrentTransition), transaction.atomic():
            stale.save()

    def test_atomic_block_rolls_back_other_database_changes(self):
        first = ConcurrentJob.objects.create()
        stale = ConcurrentJob.objects.get(pk=first.pk)
        first.start()
        first.save()
        with self.assertRaises(ConcurrentTransition), transaction.atomic():
            with transaction.atomic():
                ConcurrentJob.objects.create(text="must roll back")
                stale.start()
                stale.save()
        self.assertEqual(ConcurrentJob.objects.count(), 1)
        self.assertEqual(ConcurrentJob.objects.get(pk=first.pk).status, "running")


class ConcurrentDatabaseTests(TestCase):
    databases = {"default", "secondary"}

    def test_conflict_check_uses_the_save_database(self):
        default = ConcurrentJob.objects.create(pk=1)
        first = ConcurrentJob.objects.using("secondary").create(pk=1)
        stale = ConcurrentJob.objects.using("secondary").get(pk=1)
        first.start()
        first.save(using="secondary")
        stale.start()
        with (
            self.assertRaises(ConcurrentTransition),
            transaction.atomic(using="secondary"),
        ):
            stale.save(using="secondary")
        default.start()
        default.save(using="default")
        self.assertEqual(
            ConcurrentJob.objects.using("default").get(pk=1).status, "running"
        )
