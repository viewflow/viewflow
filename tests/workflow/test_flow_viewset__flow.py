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
            Permission.objects.get(codename="view_testflowviewestprocess")
        )

    def test_non_authenticated_cant_access(self):
        response = self.client.get("/permitted/")
        self.assertEqual(403, response.status_code)

        response = self.client.get("/unavailable/")
        self.assertEqual(403, response.status_code)

    def test_admin_can_view_all_flows(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get("/permitted/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/permitted/inbox/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/permitted/queue/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/permitted/archive/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/permitted/flows/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/unavailable/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/unavailable/inbox/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/unavailable/queue/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/unavailable/archive/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/unavailable/flows/")
        self.assertEqual(200, response.status_code)

    def test_user_can_view_only_permitted_flows(self):
        self.assertTrue(self.client.login(username="user", password="user"))

        response = self.client.get("/permitted/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/permitted/inbox/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/permitted/queue/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/permitted/archive/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/permitted/flows/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/unavailable/")
        self.assertEqual(403, response.status_code)

        response = self.client.get("/unavailable/inbox/")
        self.assertEqual(403, response.status_code)

        response = self.client.get("/unavailable/queue/")
        self.assertEqual(403, response.status_code)

        response = self.client.get("/unavailable/archive/")
        self.assertEqual(403, response.status_code)

        response = self.client.get("/unavailable/flows/")
        self.assertEqual(403, response.status_code)


class TestFlowViewestProcess(Process):
    class Meta:
        proxy = True


class TestFlowViewestFlow(Flow):
    process_class = TestFlowViewestProcess

    start = flow.StartHandle().Next(this.end)
    end = flow.End()


class TestUnavailableFlowViewestFlow(Flow):
    start = flow.StartHandle().Next(this.end)
    end = flow.End()


urlpatterns = [
    path('permitted/', flow.FlowAppViewset(TestFlowViewestFlow).urls),
    path('unavailable/', flow.FlowAppViewset(TestUnavailableFlowViewestFlow).urls),
]
