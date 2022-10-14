from django.test import TestCase
from viewflow import this
from viewflow.workflow import flow, STATUS


class Test(TestCase):  # noqa: D101
    def test_workflow_end(self):
        process = TestWorkflow.start.run()

        self.assertEqual(process.status, STATUS.DONE)
        self.assertIsNotNone(process.finished)

        end_task = process.task_set.filter(flow_task=TestWorkflow.end).first()
        self.assertEqual(end_task.status, STATUS.DONE)
        self.assertIsNotNone(end_task.started)
        self.assertIsNotNone(end_task.finished)
        self.assertTrue(end_task.previous.all())
        self.assertFalse(end_task.leading.all())


class TestWorkflow(flow.Flow):  # noqa: D101
    start = flow.StartHandle().Next(this.end)
    end = flow.End()
