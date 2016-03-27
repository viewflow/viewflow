from ..activation import Activation, AbstractJobActivation, STATUS
from ..compat import mock
from ..fields import get_task_ref
from ..flow import AbstractJob
from .. import test as flow_test

from celery.task.control import revoke


class JobActivation(AbstractJobActivation):
    @Activation.status.transition(
        source=[STATUS.NEW, STATUS.ASSIGNED, STATUS.SCHEDULED],
        target=STATUS.CANCELED)
    def cancel(self):
        """
        Cancel existing task
        """
        # Since we shuld have process lock grabbed at this place,
        # even if celery starts executing the task on a worker,
        # the task not started, so I think it's safe to terminate it
        revoke(self.task.external_task_id, terminate=True)
        super(AbstractJobActivation, self).cancel.original()

    def async(self):
        """
        Async task schedule
        """
        apply_kwargs = {}
        if self.flow_task._eta is not None:
            apply_kwargs['eta'] = self.flow_Task._eta(self.task)
        elif self.flow_task._delay is not None:
            delay = self.flow_task._delay
            if callable(delay):
                delay = delay(self.task)
            apply_kwargs['countdown'] = delay
        else:
            apply_kwargs['countdown'] = 1

        self.flow_task.job.apply_async(
            args=[get_task_ref(self.flow_task), self.task.process_id, self.task.pk],
            task_id=self.task.external_task_id,
            **apply_kwargs)


class Job(AbstractJob):
    activation_cls = JobActivation

    def __init__(self, *args, **kwargs):
        self._eta = None
        self._delay = None
        super(Job, self).__init__(*args, **kwargs)

    def Eta(self, eta_callable):
        """
        Expects callable that would get the task and return datatime for
        task execution
        """
        self._eta = eta_callable
        return self

    def Delay(self, delay):
        self._delay = delay
        return self


@flow_test.flow_do.register(Job)
def flow_do(flow_node, test_task, **post_kwargs):
    """
    Eager run of delayed job call
    """
    args, kwargs = flow_node._job.apply_async.call_args
    flow_node._job.apply(*args, **kwargs).get()


@flow_test.flow_patch_manager.register(Job)
def flow_patch_manager(flow_node):
    return mock.patch.object(flow_node._job, 'apply_async')
