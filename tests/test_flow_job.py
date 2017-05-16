from django.test import TestCase

from viewflow import flow
from viewflow.activation import context, Context, STATUS
from viewflow.fields import get_task_ref
from viewflow.activation import AbstractJobActivation
from viewflow.base import this, Flow
from viewflow.flow import AbstractJob


class Test(TestCase):
    def test_flow_job_decorator(self):
        act = JobTestFlow.start.run()

        with Context(throw_test_error=False):
            job_handler(
                get_task_ref(JobTestFlow.job),
                act.process.pk,
                act.process.get_task(JobTestFlow.job, status=[STATUS.SCHEDULED]).pk)

        tasks = act.process.task_set.all()
        self.assertEqual(3, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))

    def test_flow_job_decorator_error(self):
        act = JobTestFlow.start.run()

        with Context(throw_test_error=True):
            try:
                job_handler(
                    get_task_ref(JobTestFlow.job),
                    act.process.pk,
                    act.process.get_task(JobTestFlow.job, status=[STATUS.SCHEDULED]).pk)
            except ValueError:
                """Expected test error."""

        tasks = act.process.task_set.all()
        self.assertEqual(2, tasks.count())

        job_task = act.process.get_task(JobTestFlow.job, status=[STATUS.ERROR])
        self.assertIn('Expected test error', job_task.comments)


@flow.flow_job
def job_handler(activation):
    if context.throw_test_error:
        raise ValueError('Expected test error')


class JobActivation(AbstractJobActivation):
    def run_async(self):
        """Do Nothing."""


class JobTestFlow(Flow):
    start = flow.StartFunction().Next(this.job)
    job = AbstractJob(job_handler, activation_class=JobActivation).Next(this.end)
    end = flow.End()
