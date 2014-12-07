import threading
import traceback
import uuid

from django.db import transaction
from django.utils.timezone import now

from . import fsm, signals


class STATUS(object):
    ASSIGNED = 'ASSIGNED'
    CANCELED = 'CANCELED'
    DONE = 'DONE'
    ERROR = 'ERROR'
    NEW = 'NEW'
    PREPARED = 'PREPARED'
    SCHEDULED = 'SCHEDULED'
    STARTED = 'STARTED'
    UNRIPE = 'UNRIPE'


_context_stack = threading.local()


def all_leading_canceled(activation):
    non_canceled_count = activation.task.leading.exclude(status=STATUS.CANCELED).count()
    return non_canceled_count == 0


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
    Flow task state machine
    """
    status = fsm.State()

    def __init__(self, *args, **kwargs):
        """
        Activation should be available for instantiate without any
        constructor parameters
        """
        self.flow_cls, self.flow_task = None, None
        self.process, self.task = None, None

        super(Activation, self).__init__(*args, **kwargs)

    @status.setter()
    def set_status(self, value):
        if self.task:
            self.task.status = value

    @status.getter()
    def get_status(self):
        if self.task:
            return self.task.status
        return STATUS.UNRIPE

    @status.transition(source=STATUS.UNRIPE)
    def initialize(self, flow_task, task):
        self.flow_task, self.flow_cls = flow_task, flow_task.flow_cls

        self.process = self.flow_cls.process_cls._default_manager.get(flow_cls=self.flow_cls, pk=task.process_id)
        self.task = task

    @status.transition(source=STATUS.DONE)
    def activate_next(self):
        """
        Activates next connected flow tasks
        """
        raise NotImplementedError

    @status.transition(source=STATUS.DONE, target=STATUS.NEW, conditions=[all_leading_canceled])
    def undo(self):
        """
        Undo the task
        """
        self.task.save()

    @status.transition(source=STATUS.NEW, target=STATUS.CANCELED)
    def cancel(self):
        """
        Cancel existing task
        """
        self.task.finished = now()
        self.task.save()

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        """
        Instantiate and persist new flow task.
        """
        raise NotImplementedError


class StartActivation(Activation):
    @Activation.status.super()
    def initialize(self, flow_task, task):
        self.flow_task, self.flow_cls = flow_task, flow_task.flow_cls

        if task:
            self.process, self.task = task.process, task
        else:
            self.process = self.flow_cls.process_cls(flow_cls=self.flow_cls)
            self.task = self.flow_cls.task_cls(process=self.process, flow_task=self.flow_task)

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.PREPARED)
    def prepare(self):
        """
        Initialize start task for execution.

        No db changes performed. It is safe to call it on GET requests.
        """
        self.task.started = now()

    @Activation.status.transition(source=STATUS.PREPARED, target=STATUS.DONE)
    def done(self):
        """
        Creates and starts new process instance.
        """
        signals.task_started.send(sender=self.flow_cls, process=self.process, task=self.task)

        self.process.save()

        self.task.process = self.process
        self.task.finished = now()
        self.task.save()

        signals.task_finished.send(sender=self.flow_cls, process=self.process, task=self.task)
        signals.flow_started.send(sender=self.flow_cls, process=self.process, task=self.task)

        self.activate_next()

    @Activation.status.super()
    def activate_next(self):
        """
        Activate all outgoing edges.
        """
        self.flow_task._next.activate(prev_activation=self, token=self.task.token)

    @Activation.status.super()
    def undo(self):
        """
        Undo the task
        """
        self.process.status = STATUS.CANCELED
        self.process.finished = now()
        self.process.save()
        super(StartActivation, self).undo.original()


class StartViewActivation(Activation):
    """
    Start process from user request
    """

    @Activation.status.super()
    def initialize(self, flow_task, task):
        self.flow_task, self.flow_cls = flow_task, flow_task.flow_cls

        if task:
            self.process, self.task = task.process, task
        else:
            self.process = self.flow_cls.process_cls(flow_cls=self.flow_cls)
            self.task = self.flow_cls.task_cls(process=self.process, flow_task=self.flow_task)

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.PREPARED)
    def prepare(self):
        """
        Initialize start task for execution.

        No db changes performed. It is safe to call it on GET requests.
        """
        self.task.started = now()

    @Activation.status.transition(source=STATUS.PREPARED, target=STATUS.DONE)
    def done(self):
        """
        Creates and starts new process instance.
        """
        signals.task_started.send(sender=self.flow_cls, process=self.process, task=self.task)

        self.process.save()

        self.task.process = self.process
        self.task.finished = now()
        self.task.save()

        signals.task_finished.send(sender=self.flow_cls, process=self.process, task=self.task)

        self.activate_next()

    @Activation.status.super()
    def activate_next(self):
        """
        Activate all outgoing edges.
        """
        self.flow_task._next.activate(prev_activation=self, token=self.task.token)


class ViewActivation(Activation):
    @Activation.status.transition(source=STATUS.NEW, target=STATUS.ASSIGNED)
    def assign(self, user=None):
        """
        Assign user to the task
        """
        if user:
            self.task.owner = user
        self.task.save()

    @Activation.status.transition(source=STATUS.ASSIGNED, target=STATUS.NEW)
    def unassign(self):
        """
        Remove user from the task assignment
        """
        self.task.owner = None
        self.task.save()

    @Activation.status.transition(source=STATUS.ASSIGNED)
    def reassign(self, user=None):
        """
        Reassign another user
        """
        if user:
            self.task.owner = user
        self.task.save()

    @Activation.status.transition(source=STATUS.ASSIGNED, target=STATUS.PREPARED)
    def prepare(self):
        """
        Initialize start task for execution.

        No db changes performed. It is safe to call it on GET requests.
        """
        self.task.started = now()

    @Activation.status.transition(source=STATUS.PREPARED, target=STATUS.DONE)
    def done(self):
        signals.task_started.send(sender=self.flow_cls, process=self.process, task=self.task)

        self.task.finished = now()
        self.task.save()

        signals.task_finished.send(sender=self.flow_cls, process=self.process, task=self.task)

        self.activate_next()

    @Activation.status.super()
    def activate_next(self):
        """
        Activate all outgoing edges.
        """
        self.flow_task._next.activate(prev_activation=self, token=self.task.token)

    @classmethod
    def create_task(cls, flow_task, prev_activation, token):
        return flow_task.flow_cls.task_cls(
            process=prev_activation.process,
            flow_task=flow_task,
            token=token)

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        """
        Instantiate new task
        """
        task = cls.create_task(flow_task, prev_activation, token)

        task.save()
        task.previous.add(prev_activation.task)

        activation = cls()
        activation.initialize(flow_task, task)

        return activation


class AbstractGateActivation(Activation):
    def calculate_next(self):
        """
        Calculate next tasks for activation
        """
        raise NotImplementedError

    @Activation.status.transition(source=STATUS.NEW)
    def perform(self):
        try:
            with transaction.atomic(savepoint=True):
                self.task.started = now()
                self.task.save()

                signals.task_started.send(sender=self.flow_cls, process=self.process, task=self.task)

                self.calculate_next()

                self.task.finished = now()
                self.set_status(STATUS.DONE)
                self.task.save()

                signals.task_finished.send(sender=self.flow_cls, process=self.process, task=self.task)

                self.activate_next()
        except Exception as exc:
            if not context.propagate_exception:
                self.task.comments = "{}\n{}".format(exc, traceback.format_exc())
                self.task.finished = now()
                self.set_status(STATUS.ERROR)
                self.task.save()
                signals.task_failed.send(sender=self.flow_cls, process=self.process, task=self.task)
            else:
                raise

    @Activation.status.transition(source=STATUS.ERROR)
    def retry(self):
        self.perform.original()

    @Activation.status.transition(source=[STATUS.ERROR, STATUS.DONE], target=STATUS.NEW)
    def undo(self):
        """
        Undo the task
        """
        super(AbstractGateActivation, self).undo.original()

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
        activation.perform()

        return activation


class AbstractJobActivation(Activation):
    def async(self):
        raise NotImplementedError

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.ASSIGNED)
    def assign(self):
        self.task.started = now()
        self.task.external_task_id = str(uuid.uuid4())
        self.task.save()

    @Activation.status.transition(source=STATUS.ASSIGNED)
    def schedule(self):
        try:
            with transaction.atomic(savepoint=True):
                self.async()
                self.set_status(STATUS.SCHEDULED)
                self.task.save()
        except Exception as exc:
            if not context.propagate_exception:
                self.task.comments = "{}\n{}".format(exc, traceback.format_exc())
                self.task.finished = now()
                self.set_status(STATUS.ERROR)
                self.task.save()
            else:
                raise

    @Activation.status.transition(source=STATUS.SCHEDULED, target=STATUS.STARTED)
    def start(self):
        self.task.started = now()
        self.task.save()
        signals.task_started.send(sender=self.flow_cls, process=self.process, task=self.task)

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.DONE)
    def done(self):
        self.task.finished = now()
        self.set_status(STATUS.DONE)
        self.task.save()

        signals.task_finished.send(sender=self.flow_cls, process=self.process, task=self.task)

        self.activate_next()

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.ERROR)
    def error(self, comments=""):
        self.task.comments = comments
        self.task.finished = now()
        self.task.save()
        signals.task_failed.send(sender=self.flow_cls, process=self.process, task=self.task)

    @Activation.status.transition(source=[STATUS.SCHEDULED, STATUS.STARTED, STATUS.ERROR])
    def retry(self):
        self.schedule.original()

    @Activation.status.transition(
        source=[STATUS.SCHEDULED, STATUS.STARTED, STATUS.ERROR, STATUS.DONE],
        target=STATUS.ASSIGNED)
    def undo(self):
        """
        Undo the task
        """
        super(AbstractJobActivation, self).undo.original()

    @Activation.status.transition(source=[STATUS.NEW, STATUS.ASSIGNED], target=STATUS.CANCELED)
    def cancel(self):
        """
        Cancel existing task
        """
        super(AbstractJobActivation, self).cancel.original()

    @Activation.status.super()
    def activate_next(self):
        """
        Activate all outgoing edges.
        """
        self.flow_task._next.activate(prev_activation=self, token=self.task.token)

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
        activation.assign()
        activation.schedule()

        return activation


class EndActivation(Activation):
    @Activation.status.transition(source=STATUS.NEW, target=STATUS.DONE)
    def perform(self):
        with transaction.atomic(savepoint=True):
            self.task.started = now()
            self.task.save()

            signals.task_started.send(sender=self.flow_cls, process=self.process, task=self.task)

            self.process.status = STATUS.DONE
            self.process.finished = now()
            self.process.save()

            for task in self.process.active_tasks():
                if task != self.task:
                    task.activate().cancel()

            self.task.finished = now()
            self.task.save()

            signals.task_finished.send(sender=self.flow_cls, process=self.process, task=self.task)
            signals.flow_finished.send(sender=self.flow_cls, process=self.process, task=self.task)

    @Activation.status.super()
    def undo(self):
        """
        Undo the task
        """
        self.process.status = STATUS.NEW
        self.process.finished = None
        self.process.save()
        super(EndActivation, self).undo.original()

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
        activation.perform()

        return activation
