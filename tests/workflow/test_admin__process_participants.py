from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.db import connection
from django.test import RequestFactory, TestCase
from django.test.utils import CaptureQueriesContext

from viewflow import this
from viewflow.workflow import Flow, flow
from viewflow.workflow.admin import ProcessAdmin
from viewflow.workflow.fields import get_flow_ref
from viewflow.workflow.flow import views
from viewflow.workflow.models import Process


class TestParticipantsProcess(Process):
    class Meta:
        proxy = True


class TestParticipantsFlow(Flow):  # noqa: D101
    process_class = TestParticipantsProcess

    start = flow.StartHandle().Next(this.task)
    task = (
        flow.View(views.UpdateProcessView.as_view(fields=[]))
        .Assign(this.assign_owner)
        .Next(this.end)
    )
    end = flow.End()

    def assign_owner(self, activation):
        return User.objects.get(username="alice")


class Test(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user("alice", password="pwd")

    def _query_count_for_n_processes(self, n):
        for _ in range(n):
            TestParticipantsFlow.start.run()

        admin_instance = ProcessAdmin(Process, AdminSite())
        request = RequestFactory().get("/")

        with CaptureQueriesContext(connection) as ctx:
            queryset = admin_instance.get_queryset(request)
            for process in queryset:
                admin_instance.participants(process)
        return len(ctx)

    def test_participants_shows_the_task_owner(self):
        TestParticipantsFlow.start.run()

        admin_instance = ProcessAdmin(Process, AdminSite())
        request = RequestFactory().get("/")
        process = admin_instance.get_queryset(request).get()

        self.assertEqual(admin_instance.participants(process), "alice")

    def test_flow_class_filter_choices_render(self):
        # regression: the stock flow_class list_filter built its choices from
        # the admin queryset, executing the participants prefetch against
        # materialized flow classes (viewflow/viewflow#523)
        TestParticipantsFlow.start.run()

        admin_instance = ProcessAdmin(Process, AdminSite())
        request = RequestFactory().get("/")
        request.user = User.objects.create_superuser("root", password="pwd")

        changelist = admin_instance.get_changelist_instance(request)
        choices = [
            choice
            for spec in changelist.filter_specs
            for choice in spec.choices(changelist)
        ]
        self.assertTrue(
            any(TestParticipantsFlow.process_title in str(c) for c in choices)
        )

    def test_flow_class_filter_narrows_the_changelist(self):
        TestParticipantsFlow.start.run()

        admin_instance = ProcessAdmin(Process, AdminSite())
        request = RequestFactory().get(
            "/", {"flow_class": get_flow_ref(TestParticipantsFlow)}
        )
        request.user = User.objects.create_superuser("root", password="pwd")

        changelist = admin_instance.get_changelist_instance(request)
        self.assertEqual(changelist.get_queryset(request).count(), 1)

    def test_changelist_avoids_a_query_per_row(self):
        with_2 = self._query_count_for_n_processes(2)
        with_5 = self._query_count_for_n_processes(5)

        self.assertEqual(with_2, with_5)
