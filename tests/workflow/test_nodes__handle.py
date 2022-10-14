from django.test import TestCase

from viewflow import this, jsonstore
from viewflow.workflow import flow
from viewflow.workflow.models import Process
from viewflow.workflow.status import STATUS


class Test(TestCase):  # noqa: D101
    def test_handler_succeed(self):
        process = TestWorkflow.start.run(raise_exception=False)

        task = process.task_set.filter(flow_task=TestWorkflow.handle).first()
        self.assertIsNotNone(task)

        TestWorkflow.handle.run(task)
        task.refresh_from_db()
        self.assertEqual(task.status, STATUS.DONE)

        process.refresh_from_db()
        self.assertEqual(process.status, STATUS.DONE)
        self.assertEqual(process.task_set.count(), 3)

    def test_handler_exception(self):
        process = TestWorkflow.start.run(raise_exception=True)

        task = process.task_set.filter(flow_task=TestWorkflow.handle).first()
        self.assertIsNotNone(task)
        try:
            TestWorkflow.handle.run(task)
        except Exception:
            self.assertEqual(task.status, STATUS.NEW)
            task.refresh_from_db()
            self.assertEqual(task.status, STATUS.NEW)
        else:
            self.fail()


class TestWorkflowHandlerProcess(Process):
    raise_exception = jsonstore.BooleanField()

    class Meta:
        proxy = True


class TestWorkflow(flow.Flow):  # noqa: D101
    process_class = TestWorkflowHandlerProcess

    start = flow.StartHandle(this.start_process).Next(this.handle)

    handle = flow.Handle(this.handler).Next(this.end)

    end = flow.End()

    def start_process(self, activation, raise_exception=False):
        activation.process.raise_exception = raise_exception
        return activation.process

    def handler(self, activation):
        if activation.process.raise_exception:
            raise Exception('Flow execution runtime exception')
