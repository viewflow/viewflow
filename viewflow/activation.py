import threading
from django.db import transaction
from celery.utils import uuid

from viewflow import signals
from viewflow.fields import get_task_ref


_context_stack = threading.local()


class Context(object):
    """
    Thread-local activation context, dynamically scoped

    :keyword propagate_exception: If True on activation fails exception would be propagated to previous activalion,
    if False, current task activation would be marked as failed

    Usage ::

        with Context(propagate_exception=False):
             print(context.propagate_exception)  # prints 'False'
        print(context.propagate_exception)  # prints default 'True'
    """
    def __init__(self, default=None, **kwargs):
        self.default = default
        self.current_context_data = kwargs

    def __getattr__(self, name):
        stack = []

        if hasattr(_context_stack, 'data'):
            stack = _context_stack.data

        for scope in reversed(stack):
            if name in scope:
                return scope[name]

        if name in self.default:
            return self.default[name]

        raise AttributeError(name)

    def __enter__(self):
        if not hasattr(_context_stack, 'data'):
            _context_stack.data = []
        _context_stack.data.append(self.current_context_data)

    def __exit__(self, t, v, tb):
        _context_stack.data.pop()

    @staticmethod
    def create(**kwargs):
        return Context(default=kwargs)


context = Context.create(propagate_exception=True)


class Activation(object):
    """
    Activation is responsible for managing livecycle and persistance of flow task instance
    """

    def __init__(self, **kwargs):
        """
        Activation should be available for instance without any constructor parameters.
        """
        self.flow_cls, self.flow_task = None, None
        self.process, self.task = None, None

        super(Activation, self).__init__(**kwargs)

    def activate_next(self):
        """
        Activates next connected flow tasks
        """
        raise NotImplementedError

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        """
        Instantiate and persist new flow task.
        """
        raise NotImplementedError


class StartActivation(Activation):
    """
    Base activation that creates new process instance.

    Start activations could not be activated by other tasks.
    """

    def initialize(self, flow_task):
        """
        Initialize new activation instance.
        """
        self.flow_task, self.flow_cls = flow_task, flow_task.flow_cls

        self.process = self.flow_cls.process_cls(flow_cls=self.flow_cls)
        self.task = self.flow_cls.task_cls(process=self.process, flow_task=self.flow_task)

    def prepare(self):
        """
        Initialize start task for execution.

        No db changes performed. It is safe to call it on GET requests.
        """
        self.task.prepare()
        signals.task_prepared.send(sender=self.flow_cls, process=self.process, task=self.task)

    def done(self, process=None, user=None):
        """
        Creates and starts new process instance.
        """
        if process:
            self.process = process
        self.process.save()

        self.task.process = self.process
        if user:
            self.task.owner = user
        self.task.done()
        self.task.save()

        self.process.start()
        self.process.save()

        signals.flow_started.send(sender=self.flow_cls, process=self.process, task=self.task)
        signals.task_finished.send(sender=self.flow_cls, process=self.process, task=self.task)

        self.activate_next()

    def activate_next(self):
        """
        Activate all outgoing edges.
        """
        for outgoing in self.flow_task._outgoing():
            outgoing.dst.activate(prev_activation=self, token=self.task.token)


class TaskActivation(Activation):
    """
    Base class for flow tasks that do some work.
    """

    def initialize(self, flow_task, task):
        """
        Initialize new activation instance.
        """
        self.flow_task, self.flow_cls = flow_task, flow_task.flow_cls

        self.process = self.flow_cls.process_cls._default_manager.get(flow_cls=self.flow_cls, pk=task.process_id)
        self.task = task

    def prepare(self):
        """
        Initialize task for execution.

        No db changes performed. It is safe to call it on GET requests.
        """
        self.task.prepare()
        signals.task_prepared.send(sender=self.flow_cls, process=self.process, task=self.task)

    def done(self):
        """
        Finishes the task and activates next.
        """
        self.task.done()
        self.task.save()
        signals.task_finished.send(sender=self.flow_cls, process=self.process, task=self.task)

        self.activate_next()

    def activate_next(self):
        """
        Activate all outgoing edges.
        """
        for outgoing in self.flow_task._outgoing():
            outgoing.dst.activate(prev_activation=self, token=self.task.token)


class ViewActivation(TaskActivation):
    """
    Activation for task performed by human in django views
    """

    def assign(self, user):
        """
        Assigns the user to the task.
        """
        self.task.assign(user=user)
        self.task.save()

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        """
        Instantiate new task, calculate and store required user permissions.

        If task can be assigned to user, assigns it.
        """

        flow_cls, flow_task = flow_task.flow_cls, flow_task
        process = prev_activation.process

        task = flow_cls.task_cls(
            process=process,
            flow_task=flow_task,
            token=token)

        # Try to assign permission
        owner_permission = flow_task.calc_owner_permission(task)
        if owner_permission:
            task.owner_permission = owner_permission

        task.save()
        task.previous.add(prev_activation.task)

        activation = cls()
        activation.initialize(flow_task, task)

        # Try to assign owner
        owner = flow_task.calc_owner(task)
        if owner:
            activation.assign(owner)

        return activation


class JobActivation(TaskActivation):
    """
    Activation for long-running background celery tasks.
    """
    fail_on_children_error = False

    def assign(self, external_task_id):
        """
        Saves scheduled celery task_id.
        """
        self.task.assign(external_task_id=external_task_id)
        self.task.save()

    def schedule(self, task_id):
        """
        Async task schedule
        """
        self.flow_task.job.apply_async(
            args=[get_task_ref(self.flow_task), self.task.process_id, self.task.pk],
            task_id=task_id,
            countdown=1)

    def start(self):
        """
        Persist that job is started
        """
        self.task.start()
        self.task.save()
        signals.task_started.send(sender=self.flow_cls, process=self.process, task=self.task)

    def error(self, exc):
        self.task.error()
        self.task.save()
        signals.task_failed.send(sender=self.flow_cls, process=self.process, task=self.task, exeception=exc)

    def done(self, result):
        """
        Celery task finished with `result`, finishes the flow task
        """
        with Context(propagate_exception=False):
            super(JobActivation, self).done()

    def activate_next(self):
        """
        If Job is successfully completed, next task activation failure can't drop this
        """
        with Context(propagate_exception=False):
            super(JobActivation, self).activate_next()

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        """
        Activate and schedule for background job execution.

        It is safe to schedule job just now b/c the process instance is locked,
        and job will wait until this transaction completes.
        """
        flow_cls, flow_task = flow_task.flow_cls, flow_task
        process = prev_activation.process

        task = flow_cls.task_cls(
            process=process,
            flow_task=flow_task,
            token=token)

        task.save()
        task.previous.add(prev_activation.task)

        activation = cls()
        activation.initialize(flow_task, task)

        external_task_id = uuid()
        activation.assign(external_task_id)
        activation.schedule(external_task_id)

        return activation


class GateActivation(Activation):
    """
    Activation for task gates.
    """
    def initialize(self, flow_task, task):
        self.flow_task, self.flow_cls = flow_task, flow_task.flow_cls

        self.process = self.flow_cls.process_cls._default_manager.get(flow_cls=self.flow_cls, pk=task.process_id)
        self.task = task

    def prepare(self):
        self.task.prepare()
        signals.task_prepared.send(sender=self.flow_cls, process=self.process, task=self.task)

    def start(self):
        self.task.start()
        self.task.save()
        signals.task_started.send(sender=self.flow_cls, process=self.process, task=self.task)

    def execute(self):
        """
        Execute gate conditions, prepare data required to determine
        next tasks for activation.
        """
        raise NotImplementedError

    def error(self, exc):
        self.task.error()
        self.task.save()
        signals.task_failed.send(sender=self.flow_cls, process=self.process, task=self.task, exeception=exc)

    def done(self):
        self.task.done()
        self.task.save()
        signals.task_finished.send(sender=self.flow_cls, process=self.process, task=self.task)

        self.activate_next()

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        """
        Activates gate, executes it immediately, and activates next tasks.
        """
        flow_cls, flow_task = flow_task.flow_cls, flow_task
        process = prev_activation.process

        task = flow_cls.task_cls(
            process=process,
            flow_task=flow_task,
            token=token)

        task.save()
        task.previous.add(prev_activation.task)

        activation = cls()
        activation.initialize(flow_task, task)
        activation.prepare()

        if context.propagate_exception:
            """
            Any execution exception would be propagated back,
            assume that rollback will happens and no task activation would be stored
            """
            activation.execute()
            activation.done()
        else:
            """
            On error, save the task and not propagate exception on top
            """
            try:
                with transaction.atomic(savepoint=True):
                    activation.execute()
            except Exception as exc:
                activation.error(exc)

        return activation


class EndActivation(Activation):
    """
    Activation that finishes the process, and cancels all other active tasks.
    """
    def initialize(self, flow_task, task):
        """
        Initialize new activation instance.
        """
        self.flow_task, self.flow_cls = flow_task, flow_task.flow_cls

        self.process = self.flow_cls.process_cls._default_manager.get(flow_cls=self.flow_cls, pk=task.process_id)
        self.task = task

    def prepare(self):
        self.task.prepare()
        signals.task_prepared.send(sender=self.flow_cls, process=self.process, task=self.task)

    def done(self):
        self.task.done()
        self.task.save()

        self.process.finish()
        self.process.save()

        for task in self.process.active_tasks():
            task.flow_task.deactivate(task)

        signals.task_finished.send(sender=self.flow_cls, process=self.process, task=self.task)
        signals.flow_finished.send(sender=self.flow_cls, process=self.process, task=self.task)

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        """
        Mark process as done, and cancel all other active tasks.
        """
        flow_cls, flow_task = flow_task.flow_cls, flow_task
        process = prev_activation.process

        task = flow_cls.task_cls(
            process=process,
            flow_task=flow_task,
            token=token)

        task.save()
        task.previous.add(prev_activation.task)

        activation = cls()
        activation.initialize(flow_task, task)
        activation.prepare()
        activation.done()

        return activation
