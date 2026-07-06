from django.test import TestCase

from viewflow import this, jsonstore
from viewflow.workflow import flow
from viewflow.workflow.context import Context
from viewflow.workflow.models import Process
from viewflow.workflow.status import STATUS


class Test(TestCase):  # noqa: D101
    def test_partial_write_is_rolled_back_when_task_errors_in_async_mode(self):
        # propagate_exception=False mirrors how a JOB node's completion
        # activates the next node (nodes/job.py AbstractJobActivation.execute):
        # a downstream error must not propagate, it is recorded on the task.
        with Context(propagate_exception=False):
            process = TestWorkflow.start.run()

        task = process.task_set.get(flow_task=TestWorkflow.func)
        self.assertEqual(task.status, STATUS.ERROR)

        process.refresh_from_db()
        # The process.save() that ran before the raise must be rolled back
        # by the savepoint together with the rest of the failed activation,
        # not committed alongside the ERROR marker.
        self.assertIsNone(process.marker)


class TestWorkflowFuncProcess(Process):
    marker = jsonstore.CharField()

    class Meta:
        proxy = True


class TestWorkflow(flow.Flow):  # noqa: D101
    process_class = TestWorkflowFuncProcess

    start = flow.StartHandle().Next(this.func)
    func = flow.Function(this.raise_after_partial_write).Next(this.end)
    end = flow.End()

    def raise_after_partial_write(self, activation):
        activation.process.marker = "changed"
        activation.process.save()
        raise ValueError("boom")
