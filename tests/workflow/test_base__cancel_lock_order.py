from contextlib import contextmanager

from django.db import transaction
from django.test import TransactionTestCase

from viewflow import this
from viewflow.workflow import PROCESS, Flow, flow, lock


events = []


class RecordingCacheLock(lock.CacheLock):
    # Registers an on_commit hook inside the locked transaction and records
    # when the lock is actually released (cache key deleted), so the test
    # can compare release position against the transaction commit.
    @contextmanager
    def __call__(self, flow_class, process_pk):
        with super().__call__(flow_class, process_pk):
            transaction.on_commit(lambda: events.append("transaction_committed"))
            yield
        events.append("lock_released")


class TestCancelLockOrderFlow(Flow):  # noqa: D101
    lock_impl = RecordingCacheLock()

    start = flow.StartHandle().Next(this.task)
    task = flow.Handle(this.noop).Next(this.end)
    end = flow.End()

    def noop(self, activation):
        pass


class TestFlowCancelLockOrder(TransactionTestCase):
    def test_lock_released_only_after_cancel_transaction_commits(self):
        # Flow.cancel did `with transaction.atomic(), self.lock(process.pk):`
        # -- entering the transaction *before* the lock, so on exit a
        # CacheLock's key was deleted *before* cancel's writes committed. A
        # concurrent task completion could acquire the freed lock, read the
        # pre-cancel snapshot, and complete tasks on a process that is being
        # canceled. Same bug class already fixed in wrap_task_view.
        process = TestCancelLockOrderFlow.start.run()
        events.clear()  # drop the lock cycle from starting the process

        TestCancelLockOrderFlow.instance.cancel(process)

        self.assertEqual(
            events,
            ["transaction_committed", "lock_released"],
            "the lock must be released only after the transaction commits",
        )
        process.refresh_from_db()
        self.assertEqual(process.status, PROCESS.CANCELED)
