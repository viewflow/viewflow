from django.contrib.auth.models import User, Permission
from django.test import TestCase, override_settings
from django.urls import path

from viewflow import this
from viewflow.workflow import Flow, flow
from viewflow.workflow.models import Process


@override_settings(ROOT_URLCONF=__name__)
class TestFlowChartPermission(TestCase):
    # FlowChartView had no auth/permission check of its own, relying
    # entirely on SiteMiddleware's app gate -- which is absent for a
    # standalone FlowViewset (the documented mount pattern used here,
    # e.g. tests/workflow/test_nodes__split.py), so an anonymous user
    # could see both the static flow chart and, via <pk>/chart/, a
    # specific process's task-status-colored progress.
    @classmethod
    def setUpTestData(cls):
        cls.viewer = User.objects.create_user(username="viewer", password="pwd")
        cls.viewer.user_permissions.add(
            Permission.objects.get(codename="view_testflowchartprocess")
        )

    def _start_process(self):
        return TestFlowChartFlow.start.run()

    def test_anonymous_user_cannot_view_the_flow_chart(self):
        response = self.client.get("/chart/")
        self.assertEqual(403, response.status_code)

    def test_anonymous_user_cannot_view_a_process_chart(self):
        process = self._start_process()

        response = self.client.get(f"/{process.pk}/chart/")
        self.assertEqual(403, response.status_code)

    def test_permitted_user_can_view_the_flow_chart(self):
        process = self._start_process()
        self.assertTrue(self.client.login(username="viewer", password="pwd"))

        response = self.client.get("/chart/")
        self.assertEqual(200, response.status_code)

        response = self.client.get(f"/{process.pk}/chart/")
        self.assertEqual(200, response.status_code)


class TestFlowChartProcess(Process):
    class Meta:
        proxy = True


class TestFlowChartFlow(Flow):
    process_class = TestFlowChartProcess

    start = flow.StartHandle().Next(this.end)
    end = flow.End()


urlpatterns = [path("", flow.FlowViewset(TestFlowChartFlow).urls)]
