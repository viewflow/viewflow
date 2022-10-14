from django.contrib.auth.models import User
from django.urls import path
from django.test import TestCase, override_settings

from viewflow import this
from viewflow.workflow import flow, PROCESS, STATUS
from viewflow.workflow.flow import views


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(username="admin", password="admin")

    def reverse(self, flow_task, name):
        task = TestUndoFlow.task_class.objects.get(flow_task=flow_task)
        return flow_task.reverse(name, args=[task.process_id, task.pk])

    def test_undo_human_tasks(self):
        # forward flow
        self.assertTrue(self.client.login(username="admin", password="admin"))
        self.assertRedirects(
            self.client.post(
                "/workflow/start/",
                {
                    "text": "Hello, world",
                    "_viewflow_activation-started": "2000-01-01",
                    "_continue": 1,
                },
            ),
            self.reverse(TestUndoFlow.task, "index"),
            fetch_redirect_response=False,
        )
        self.assertRedirects(
            self.client.post(
                self.reverse(TestUndoFlow.task, "assign"), {"_continue": 1}
            ),
            self.reverse(TestUndoFlow.task, "index"),
            fetch_redirect_response=False,
        )
        self.assertEqual(
            self.client.post(
                self.reverse(TestUndoFlow.task, "execute"),
                {"_viewflow_activation-started": "2000-01-01"},
            ).status_code,
            302,
        )

        # undo process finale
        process = TestUndoFlow.process_class.objects.get()
        end_task = process.task_set.get(flow_task=TestUndoFlow.end)
        with end_task.activation() as activation:
            activation.undo()

        # undo task
        task = process.task_set.get(flow_task=TestUndoFlow.task)
        with task.activation() as activation:
            activation.undo()

        # revive task
        with task.activation() as activation:
            activation.revive()

        # cancel task
        task = process.task_set.get(flow_task=TestUndoFlow.task, status=STATUS.NEW)
        with task.activation() as activation:
            activation.cancel()

        # undo process start _
        start_task = process.task_set.get(flow_task=TestUndoFlow.start)
        with start_task.activation() as activation:
            activation.undo()

        process.refresh_from_db()
        self.assertTrue(process.finished)
        self.assertEqual(PROCESS.CANCELED, process.status)


class TestUndoFlow(flow.Flow):
    start = flow.Start(views.CreateProcessView.as_view(fields=[])).Next(this.task)
    task = flow.View(views.UpdateProcessView.as_view(fields=[])).Next(this.end)
    end = flow.End()


urlpatterns = [path("workflow/", flow.FlowViewset(TestUndoFlow).urls)]
