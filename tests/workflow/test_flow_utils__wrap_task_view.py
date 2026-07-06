from contextlib import contextmanager

from django.db import transaction
from django.http import HttpResponse
from django.test import TransactionTestCase, override_settings
from django.urls import path
from django.views import View

from viewflow import this
from viewflow.workflow import Flow, flow, lock
from viewflow.workflow.flow.utils import wrap_task_view


events = []


class RecordingCacheLock(lock.CacheLock):
    # Records when the lock is actually released (cache key deleted), so
    # the test can compare its position against when the wrapping
    # transaction commits.
    @contextmanager
    def __call__(self, flow_class, process_pk):
        with super().__call__(flow_class, process_pk):
            yield
        events.append("lock_released")


class RecordingView(View):
    def post(self, request, *args, **kwargs):
        transaction.on_commit(lambda: events.append("transaction_committed"))
        return HttpResponse("ok")


class TestLockOrderFlow(Flow):
    lock_impl = RecordingCacheLock()

    start = flow.StartHandle().Next(this.task)
    task = flow.Handle(this.noop).Next(this.end)
    end = flow.End()

    def noop(self, activation):
        pass


urlpatterns = [
    path(
        "<int:process_pk>/task/<int:task_pk>/action/",
        wrap_task_view(TestLockOrderFlow.task, RecordingView.as_view()),
    ),
]


@override_settings(ROOT_URLCONF=__name__)
class TestWrapTaskViewLockOrder(TransactionTestCase):
    def test_lock_released_only_after_transaction_commits(self):
        # wrap_task_view did `with transaction.atomic(), self.flow_class.lock(process_pk):`
        # -- entering the transaction *before* the lock, so on exit the lock
        # is released *before* the transaction commits. A concurrent request
        # could then acquire the freed lock and read pre-commit (stale) data,
        # double-executing task actions. wrap_view (the sibling wrapper for
        # human View tasks) already gets this right.
        process = TestLockOrderFlow.start.run()
        task = process.task_set.get(flow_task=TestLockOrderFlow.task)
        events.clear()  # drop the lock cycle from starting the process

        response = self.client.post(f"/{process.pk}/task/{task.pk}/action/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            events,
            ["transaction_committed", "lock_released"],
            "the lock must be released only after the transaction commits",
        )
