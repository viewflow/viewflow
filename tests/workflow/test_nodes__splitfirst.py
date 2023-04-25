from django.urls import path
from django.test import TestCase, override_settings

from viewflow import this, jsonstore
from viewflow.workflow import flow, act
from viewflow.workflow.flow import FlowViewset
from viewflow.workflow.models import Process
from viewflow.workflow.status import STATUS


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):  # noqa: D101
    def test_first_task_cancels_others(self):
        pass


class TestWorkflow(flow.Flow):  # noqa: D101
    start = flow.StartHandle(this.start_process).Next(this.split)

    split = flow.SplitFirst().Next(this.case_1).Next(this.case_2)

    case_1 = flow.Handle(this.handle).Next(this.continue_1)
    case_2 = flow.Handle(this.handle).Next(this.continue_2)

    continue_1 = flow.Handle(this.handle).Next(this.end)
    continue_2 = flow.Handle(this.handle).Next(this.end)

    end = flow.End()

    def handle(self, activation):
        pass


urlpatterns = [path("", FlowViewset(TestWorkflow).urls)]
