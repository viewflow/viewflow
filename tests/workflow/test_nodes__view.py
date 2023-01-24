from django.contrib.auth.models import User
from django.urls import path
from django.test import TestCase, override_settings

from viewflow import this
from viewflow.workflow import flow
from viewflow.workflow.flow import FlowAppViewset, views
from viewflow.workflow.status import STATUS


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):  # noqa: D101
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@admin.com", "admin")
        self.assertTrue(self.client.login(username="admin", password="admin"))

    def test_view_node_lifecycle(self):
        # init
        self.assertTrue(TestWorkflow.approve._owner_permission_auto_create)
        self.assertEqual(
            TestWorkflow.approve._owner_permission, "viewflow.can_approve_process"
        )

        # start
        process = TestWorkflow.start.run()
        start_task = process.task_set.filter(flow_task=TestWorkflow.start).first()
        with start_task.activation() as activation:
            transitions = activation.get_available_transitions(self.admin)
            self.assertEqual([], transitions)

        # approve task created
        task = process.task_set.filter(flow_task=TestWorkflow.approve).first()
        self.assertIsNotNone(task)
        self.assertEqual(task.flow_task_type, "HUMAN")
        self.assertEqual(task.status, STATUS.NEW)
        self.assertIsNone(task.owner)
        self.assertEqual(task.owner_permission, "viewflow.can_approve_process")
        self.assertIn(task, TestWorkflow.task_class.objects.user_queue(self.admin))
        self.assertTrue(getattr(TestWorkflow, "_on_create_executed", False))
        with task.activation() as activation:
            transitions = activation.get_available_transitions(self.admin)
            self.assertEqual(
                ["assign", "cancel"], [transition.slug for transition in transitions]
            )

        # execute unassigned node fails
        execute_url = TestWorkflow.approve.reverse(
            "execute", args=[process.pk, task.pk]
        )
        response = self.client.get(execute_url)
        self.assertEqual(
            response.status_code, 403, "Should not allow to execute task before assign"
        )

        # assign redirect to detail
        index_url = TestWorkflow.approve.reverse("index", args=[process.pk, task.pk])
        assign_url = TestWorkflow.approve.reverse("assign", args=[process.pk, task.pk])
        self.assertEqual(assign_url, f"/{task.process_id}/approve/{task.pk}/assign/")
        response = self.client.post(assign_url, {"_continue": 1})
        self.assertRedirects(response, index_url, fetch_redirect_response=False)

        # execute assigned node succeed
        execute_url = TestWorkflow.approve.reverse(
            "execute", args=[process.pk, task.pk]
        )
        response = self.client.get(execute_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(execute_url, {"_continue": 1})
        self.assertEquals(response.status_code, 302)

        # check
        process.refresh_from_db()
        self.assertEqual(process.status, STATUS.DONE)


class TestWorkflow(flow.Flow):  # noqa: D101
    start = flow.StartHandle().Next(this.approve)

    approve = (
        flow.View(views.UpdateProcessView.as_view(fields=[]))
        .Permission(auto_create=True)
        .onCreate(this.toggle_on_create)
        .Next(this.end)
    )

    end = flow.End()

    def toggle_on_create(self, activation):
        assert not hasattr(self.__class__, "_on_create_executed")
        self.__class__._on_create_executed = True


urlpatterns = [path("", FlowAppViewset(TestWorkflow).urls)]
