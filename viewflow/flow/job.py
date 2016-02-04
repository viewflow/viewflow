"""
Background job executed by celery
"""
import functools
import traceback

from ..activation import AbstractJobActivation, STATUS
from ..fields import import_task_by_ref
from . import base


def flow_job(**lock_args):
    """
    Decorator that prepares celery task for execution

    Makes celery job function with the following signature
    `(flow_task-strref, process_pk, task_pk, **kwargs)`

    Expects actual celery job function which has the following signature `(activation, **kwargs)`
    If celery task class implements activation interface, job function is
    called without activation instance `(**kwargs)`

    Process instance is locked only before and after the function execution.
    Please avoid any process state modification during the celery job.
    """
    class flow_task_decorator(object):
        def __init__(self, func, activation=None):
            self.func = func
            self.activation = activation
            functools.update_wrapper(self, func)

        def __call__(self, *args, **kwargs):
            flow_task_strref = kwargs.pop('flow_task_strref') if 'flow_task_strref' in kwargs else args[0]
            process_pk = kwargs.pop('process_pk') if 'process_pk' in kwargs else args[1]
            task_pk = kwargs.pop('task_pk') if 'task_pk' in kwargs else args[2]

            flow_task = import_task_by_ref(flow_task_strref)

            # start
            lock = flow_task.flow_cls.lock_impl(flow_task.flow_cls.instance, **lock_args)
            with lock(flow_task.flow_cls, process_pk):
                try:
                    task = flow_task.flow_cls.task_cls.objects.get(pk=task_pk)
                    if task.status == STATUS.CANCELED:
                        return
                except flow_task.flow_cls.task_cls.DoesNotExist:
                    # There was rollback on job task created transaction,
                    # we don't need to do the job
                    return
                else:
                    activation = self.activation if self.activation else flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    activation.start()

            # execute
            try:
                if self.activation:
                    result = self.func(**kwargs)
                else:
                    result = self.func(activation, **kwargs)
            except Exception as exc:
                # mark as error
                with lock(flow_task.flow_cls, process_pk):
                    task = flow_task.flow_cls.task_cls.objects.get(pk=task_pk)
                    activation = self.activation if self.activation else flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    activation.error(comments="{}\n{}".format(exc, traceback.format_exc()))
                raise
            else:
                # mark as done
                with lock(flow_task.flow_cls, process_pk):
                    task = flow_task.flow_cls.task_cls.objects.get(pk=task_pk)
                    activation = self.activation if self.activation else flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    activation.done()

                return result

        def __get__(self, instance, instancetype):
            """
            Bound methods called with self instance
            """
            if instance is None:
                return self

            func = self.func.__get__(instance, type)
            activation = instance if isinstance(instance, AbstractJobActivation) else None

            return self.__class__(func, activation=activation)

    return flow_task_decorator


class AbstractJob(base.TaskDescriptionMixin,
                  base.NextNodeMixin,
                  base.UndoViewMixin,
                  base.CancelViewMixin,
                  base.DetailsViewMixin,
                  base.Task):
    """
    Base class for task that runs in background

    Example::

        job = flow.Job(task.job) \\
            .Next(this.end)
    """
    task_type = 'JOB'

    def __init__(self, job, **kwargs):
        super(AbstractJob, self).__init__(**kwargs)
        self._job = job

    @property
    def job(self):
        return self._job
