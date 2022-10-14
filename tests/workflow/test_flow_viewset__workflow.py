from django.urls import path
from django.test import TestCase, override_settings
from django.contrib.auth.models import User, Permission

from viewflow import this
from viewflow.workflow import Flow, flow
from viewflow.workflow.models import Process


@override_settings(ROOT_URLCONF=__name__)
class TestAuth(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(username="admin", password="admin")
        cls.user = User.objects.create_user(username="user", password="user")
        cls.user.user_permissions.add(
            Permission.objects.get(codename="view_testworkflowviewestprocess")
        )

    def test_non_authenticated_cant_access(self):
        response = self.client.get("/")
        self.assertEqual(403, response.status_code)

    def test_admin_can_view_all_flows(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get("/")
        self.assertRedirects(response, "/inbox/")

        response = self.client.get("/flows/")
        self.assertRedirects(response, "/flows/testworkflowviewest/")

        response = self.client.get("/flows/testworkflowviewest/")
        self.assertEqual(
            [viewset.app_name for viewset in response.context["app"].menu_items()],
            ["testworkflowviewest", "testunavailableworkflowviewest"],
        )

    def test_user_can_view_only_permitted_flows(self):
        self.assertTrue(self.client.login(username="user", password="user"))
        response = self.client.get("/")
        self.assertRedirects(response, "/inbox/")

        response = self.client.get("/flows/")
        self.assertRedirects(response, "/flows/testworkflowviewest/")

        response = self.client.get("/flows/testworkflowviewest/")
        self.assertEqual(
            [viewset.app_name for viewset in response.context["app"].menu_items()],
            ["testworkflowviewest", "testunavailableworkflowviewest"],
        )


class TestWorkflowViewestProcess(Process):
    class Meta:
        proxy = True


class TestWorkflowViewestFlow(Flow):
    process_class = TestWorkflowViewestProcess

    start = flow.StartHandle().Next(this.end)
    end = flow.End()


class TestUnavailableWorkflowViewestFlow(Flow):
    start = flow.StartHandle().Next(this.end)
    end = flow.End()


urlpatterns = [
    path(
        "",
        flow.WorkflowAppViewset(
            flow_viewsets=[
                flow.FlowViewset(TestWorkflowViewestFlow),
                flow.FlowViewset(TestUnavailableWorkflowViewestFlow),
            ]
        ).urls,
    )
]
