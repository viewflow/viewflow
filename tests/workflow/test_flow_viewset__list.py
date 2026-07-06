from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.test.utils import CaptureQueriesContext
from django.db import connection

from viewflow import this
from viewflow.workflow import Flow, flow
from viewflow.workflow.flow import views
from viewflow.workflow.flow.views.list import FlowInboxListView, FlowQueueListView
from viewflow.workflow.models import Process


class TestListViewInboxProcess(Process):
    class Meta:
        proxy = True


class TestListViewInboxFlow(Flow):
    process_class = TestListViewInboxProcess

    start = flow.StartHandle().Next(this.task)
    task = (
        flow.View(views.UpdateProcessView.as_view(fields=[]))
        .Assign(username="inboxworker")
        .Next(this.end)
    )
    end = flow.End()


class TestListViewQueueProcess(Process):
    class Meta:
        proxy = True


class TestListViewQueueFlow(Flow):
    process_class = TestListViewQueueProcess

    start = flow.StartHandle().Next(this.task)
    task = flow.View(views.UpdateProcessView.as_view(fields=[])).Next(this.end)
    end = flow.End()


class TestFlowListViewSelectRelated(TestCase):
    # FlowInboxListView/FlowQueueListView's queryset omitted
    # select_related("process"), while their "brief" column reads
    # task.brief -> task.coerced_process -> task.process, a query per row
    # (FlowArchiveListView already select-relates). assertNumQueries pins
    # the fetch + rendering all rows' brief to a single query, regardless
    # of row count.
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("inboxworker", password="pwd")

    def test_inbox_queryset_avoids_n_plus_1_on_brief(self):
        for _ in range(4):
            TestListViewInboxFlow.start.run()

        view = FlowInboxListView()
        view.flow_class = TestListViewInboxFlow
        view.request = RequestFactory().get("/")
        view.request.user = self.user

        with self.assertNumQueries(1):
            for task in view.queryset:
                task.brief

    def _count_queries_for_n_tasks(self, n, username):
        # A fresh user per call, since guardian caches its own
        # permission-check queries per user -- reusing one user across
        # calls would make the second call look cheaper regardless of
        # row count, masking the very thing under test.
        user = User.objects.create_user(username, password="pwd")
        for _ in range(n):
            TestListViewQueueFlow.start.run()

        view = FlowQueueListView()
        view.flow_class = TestListViewQueueFlow
        view.request = RequestFactory().get("/")
        view.request.user = user

        with CaptureQueriesContext(connection) as ctx:
            for task in view.queryset:
                task.brief
        return len(ctx)

    def test_queue_queryset_avoids_n_plus_1_on_brief(self):
        # user_queue() issues its own fixed set of permission-check
        # queries (guardian lookups) unrelated to the N+1 under test, so
        # compare the query count across two row counts instead of
        # pinning an exact number -- it must not grow with row count.
        # Tasks accumulate across calls (both are visible to any
        # non-superuser), so the second call sees 2+5=7 tasks -- that's
        # fine, the assertion only needs the counts to match.
        with_2_tasks = self._count_queries_for_n_tasks(2, "queueworker1")
        with_7_tasks = self._count_queries_for_n_tasks(5, "queueworker2")

        self.assertEqual(with_2_tasks, with_7_tasks)
