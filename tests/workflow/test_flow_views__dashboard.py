from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.urls import path

from viewflow import this
from viewflow.workflow import Flow, flow
from viewflow.workflow.flow import views
from viewflow.workflow.models import Process


def _noop(activation):
    pass


class TestDashboardProcess(Process):
    class Meta:
        proxy = True


class TestDashboardFlow(Flow):
    process_class = TestDashboardProcess

    start = flow.StartHandle().Next(this.split)
    split = flow.Split().Next(this.a).Next(this.b)
    a = flow.Function(_noop).Next(this.join)
    b = flow.Handle(_noop).Next(this.join)
    join = flow.Join().Next(this.end)
    end = flow.End()


urlpatterns = [path("", flow.FlowViewset(TestDashboardFlow).urls)]


@override_settings(ROOT_URLCONF=__name__)
class TestDashboardProcessList(TestCase):
    # active_tasks() ran a fresh COUNT(*) query per process row -- N+1.
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser("admin", password="pwd")

    def _query_count_for_n_processes(self, n):
        for _ in range(n):
            TestDashboardFlow.start.run()

        self.client.force_login(self.user)
        with CaptureQueriesContext(connection) as ctx:
            self.client.get("/flows/")
        return len(ctx)

    def test_active_tasks_count_is_correct(self):
        # `b` (a Handle node) stays active/unfinished after start.run();
        # `a` completes synchronously and its completion creates `join`
        # (STARTED, waiting for `b`) -- both `b` and `join` are active.
        TestDashboardFlow.start.run()
        process = TestDashboardProcess.objects.get()
        expected = process.task_set.filter(finished__isnull=True).count()
        self.assertEqual(expected, 2)

        self.client.force_login(self.user)
        response = self.client.get("/flows/")

        object_list = list(response.context["object_list"])
        self.assertEqual(len(object_list), 1)
        self.assertEqual(object_list[0].active_tasks_count, expected)

    def test_queryset_avoids_n_plus_1_on_active_tasks(self):
        with_2 = self._query_count_for_n_processes(2)
        with_5 = self._query_count_for_n_processes(5)

        self.assertEqual(with_2, with_5)


@override_settings(ROOT_URLCONF=__name__)
class TestDashboardTaskList(TestCase):
    # process_summary() read task.process.coerced.brief with no
    # select_related("process") on the queryset -- a query per row.
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_superuser("admin2", password="pwd")

    def _query_count_for_n_processes(self, n):
        for _ in range(n):
            TestDashboardFlow.start.run()

        self.client.force_login(self.user)
        with CaptureQueriesContext(connection) as ctx:
            self.client.get("/tasks/")
        return len(ctx)

    def test_queryset_avoids_n_plus_1_on_process_summary(self):
        with_2 = self._query_count_for_n_processes(2)
        with_5 = self._query_count_for_n_processes(5)

        self.assertEqual(with_2, with_5)
