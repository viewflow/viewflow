from django.test import RequestFactory, TestCase, override_settings
from django.urls import path

from viewflow import this
from viewflow.workflow import flow
from viewflow.workflow.flow import FlowViewset
from viewflow.workflow.flow.views.actions import ReviveTaskView


def _noop(activation):
    pass


class TestReviveWorkflow(flow.Flow):  # noqa: D101
    start = flow.StartHandle().Next(this.func)
    func = flow.Function(_noop).Next(this.end)
    end = flow.End()


urlpatterns = [path("", FlowViewset(TestReviveWorkflow).urls)]


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):
    def test_get_success_url_fallback_does_not_crash(self):
        # get_success_url()'s fallback branch (self.new_task not set --
        # dead in the normal dispatch flow, since form_valid() always
        # sets it before Django's FormView redirects) called
        # super().get_get_success_url() -- a nonexistent method (double
        # "get_"), and the class also omitted TaskSuccessUrlMixin, so
        # even the intended super().get_success_url() call would have
        # hit generic.FormView's version and raised ImproperlyConfigured
        # (no success_url set).
        TestReviveWorkflow.start.run()

        task = TestReviveWorkflow.task_class.objects.get(
            flow_task=TestReviveWorkflow.func
        )
        activation = TestReviveWorkflow.func.activation_class(task)

        request = RequestFactory().get("/")
        request.activation = activation
        request.resolver_match = None

        view = ReviveTaskView()
        view.request = request

        url = view.get_success_url()

        self.assertIn(str(task.pk), url)
