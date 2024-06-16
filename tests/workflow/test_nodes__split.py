from django.urls import path
from django.test import TestCase, override_settings

from viewflow import this, jsonstore
from viewflow.workflow import flow, act
from viewflow.workflow.flow import FlowViewset
from viewflow.workflow.models import Process
from viewflow.workflow.status import STATUS


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):  # noqa: D101
    def test_split__approved(self):
        process = TestWorkflow.start.run(approved=True)
        approve_task = process.task_set.filter(flow_task=TestWorkflow.approve).first()
        self.assertEqual(approve_task.status, STATUS.NEW)
        self.assertEqual(approve_task.data, {"sample": "test task 1"})

        required_task = process.task_set.filter(flow_task=TestWorkflow.required).first()

        self.assertEqual(
            list(approve_task.previous.all()), list(required_task.previous.all())
        )

    def test_split__not_approved(self):
        process = TestWorkflow.start.run(approved=False)

        approve_task = process.task_set.filter(flow_task=TestWorkflow.approve).first()
        self.assertIsNone(approve_task)

        required_task = process.task_set.filter(flow_task=TestWorkflow.required).first()
        self.assertEqual(required_task.status, STATUS.NEW)


class TestWorkflowSplitProcess(Process):
    approved = jsonstore.BooleanField()

    class Meta:
        proxy = True


class TestWorkflow(flow.Flow):  # noqa: D101
    process_class = TestWorkflowSplitProcess

    start = flow.StartHandle(this.start_process).Next(this.split)

    split = (
        flow.Split()
        .Next(
            this.approve,
            case=act.process.approved,
            data_source=lambda activation: [{"sample": "test task 1"}],
        )
        .Next(this.required)
    )

    required = flow.Handle(this.handle)
    approve = flow.Handle(this.handle)

    def start_process(self, activation, approved=False):
        activation.process.approved = approved
        return activation.process

    def handle(self, activation):
        pass


urlpatterns = [path("", FlowViewset(TestWorkflow).urls)]
