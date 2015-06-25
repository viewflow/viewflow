from ..activation import AbstractJobActivation
from ..compat import mock
from ..fields import get_task_ref
from ..flow.job import AbstractJob
from .. import test as flow_test


class JobActivation(AbstractJobActivation):
    def schedule(self, task_id):
        """
        Async task schedule
        """
        self.flow_task.job.schedule(
            args=[get_task_ref(self.flow_task), self.task.process_id, self.task.pk],
            task_id=task_id,
            delay=1)


class Job(AbstractJob):
    activation_cls = JobActivation


@flow_test.flow_do.register(Job)
def flow_do(flow_node, test_task, **post_kwargs):
    """
    Eager run of delayed job call
    """
    args, kwargs = flow_node._job.schedule.call_args
    flow_node._job.apply(*args, **kwargs).get()


@flow_test.flow_patch_manager.register(Job)
def flow_patch_manager(flow_node):
    return mock.patch.object(flow_node._job, 'schedule')
