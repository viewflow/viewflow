from django.urls import path
from django.test import TestCase, override_settings

from viewflow import this
from viewflow.workflow import flow
from viewflow.workflow.flow import FlowViewset
from viewflow.workflow.status import STATUS, PROCESS


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):  # noqa: D101
    def test_first_task_cancels_others(self):
        process = TestWorkflow.start.run()
        task_1 = process.task_set.get(flow_task=TestWorkflow.case_1)
        task_2 = process.task_set.get(flow_task=TestWorkflow.case_2)

        TestWorkflow.case_1.run(task_1)

        task_2.refresh_from_db()
        self.assertEqual(task_2.status, STATUS.CANCELED)

        process.refresh_from_db()
        self.assertEqual(process.status, PROCESS.DONE)


class TestWorkflow(flow.Flow):  # noqa: D101
    start = flow.StartHandle().Next(this.split)

    split = flow.SplitFirst().Next(this.case_1).Next(this.case_2)

    case_1 = flow.Handle(this.handle).Next(this.end)
    case_2 = flow.Handle(this.handle).Next(this.end)

    # continue_1 = flow.Handle(this.handle).Next(this.end)
    # continue_2 = flow.Handle(this.handle).Next(this.end)

    end = flow.End()

    def handle(self, activation):
        pass


urlpatterns = [path("", FlowViewset(TestWorkflow).urls)]
