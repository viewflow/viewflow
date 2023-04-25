from contextlib import contextmanager
from typing import List

from django.db import connection, transaction
from django.utils.timezone import now

from viewflow import fsm
from .context import context
from .signals import flow_started, task_started, task_finished, task_failed
from .status import STATUS, PROCESS


def parent_tasks_completed(activation):
    """Canceled task could be recreated iff all parent task was not cancelled."""
    previous = activation.task.previous.values("status")
    completed = (STATUS.DONE, STATUS.REVIVED)
    return all(lambda task: task.status in completed, previous)


def leading_tasks_canceled(activation):
    """Task could be undone iff no outgoing uncancelled tasks are exists."""
    non_canceled_count = activation.task.leading.exclude(status=STATUS.CANCELED).count()
    return non_canceled_count == 0


def process_not_cancelled(activation):
    return activation.process.status != PROCESS.CANCELED


def has_manage_permission(activation, user):
    return activation.flow_class.instance.has_manage_permission(user)


class Activation(object):
    """
    Base class for flow task activations.

    Activation is responsible for flow task state management and persistance.
    Each activation status changes are restricted by a simple finite state
    automata.
    """

    status = fsm.State(STATUS, default=STATUS.NEW)

    def __init__(self, task):
        """Instantiate an activation."""
        self.task = task
        self.process = task.process.coerced

    def __eq__(self, other):
        if not isinstance(other, Activation):
            return False
        return self.task == other.task

    def __hash__(self):
        return hash(self.task)

    @status.setter()
    def _set_status(self, value):
        """Set the status to the underline task."""
        self.task.status = value

    @status.getter()
    def _get_status(self):
        """Get the status of the activated task."""
        return self.task.status

    @property
    def flow_task(self):
        return self.task.flow_task

    @property
    def flow_class(self):
        return self.flow_task.flow_class

    def exception_guard(self):
        """
        Perform activation action inside a transaction.

        Handle and propagate exception depending on activation context state.
        """

        @contextmanager
        def guard():
            try:
                with transaction.atomic(savepoint=True):
                    yield
            except Exception as exc:  # noqa: TODO
                if not context.propagate_exception:
                    # TODO self.task.comments = "{}\n{}".format(exc, traceback.format_exc())
                    self.task.finished = now()
                    self.set_status(STATUS.ERROR)
                    self.task.save()
                    task_failed.send(
                        sender=self.flow_class, process=self.process, task=self.task
                    )
                else:
                    raise

        return guard()

    @classmethod
    def create(cls, flow_task, prev_activation, token):
        """Instantiate and persist new flow task."""
        flow_class = flow_task.flow_class
        task = flow_class.task_class(
            process=prev_activation.process, flow_task=flow_task, token=token
        )
        task.save()
        task.previous.add(prev_activation.task)
        return cls(task)

    @status.transition(source=STATUS.NEW)
    def activate(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} class should override act() method"
        )

    @status.transition(source=STATUS.DONE)
    def create_next(self):
        raise NotImplementedError(
            f"{self.__class__.__name__} class should override create_next() method"
        )

    @status.transition(source=STATUS.NEW, target=STATUS.DONE)
    def complete(self):
        assert connection.in_atomic_block
        self.task.finished = now()
        self.task.save()
        task_finished.send(sender=self.flow_class, process=self.process, task=self.task)

    def _activate_next(self, activations: set):
        while activations:
            for current_activation in activations:
                if current_activation.activate.can_proceed():
                    current_activation.activate()

                if current_activation.complete.can_proceed():
                    current_activation.complete()

            activations = {
                next_activation
                for current_activation in activations
                if current_activation.create_next.can_proceed()
                for next_activation in current_activation.create_next()
            }

    @status.transition(source=STATUS.DONE)
    def activate_next(self):
        assert connection.in_atomic_block
        activations = set(self.create_next())
        self._activate_next(activations)

    @status.transition(
        source=STATUS.DONE,
        target=STATUS.CANCELED,
        conditions=[leading_tasks_canceled],
        permission=has_manage_permission,
    )
    def undo(self):
        self.task.finished = now()
        self.task.save()

    @status.transition(
        source=STATUS.CANCELED, target=STATUS.REVIVED, permission=has_manage_permission
    )
    def revive(self):
        """
        Recreate and activate cancelled task
        """
        flow_class = self.flow_class
        task = flow_class.task_class(
            process=self.process, flow_task=self.flow_task, token=self.task.token
        )
        task.save()

        for prev_task in self.task.previous.all():
            task.previous.add(prev_task)
        task.previous.add(self.task)

        activations = set([type(self)(task)])
        self._activate_next(activations)

    def get_outgoing_transitions(self) -> List[fsm.Transition]:
        return self.__class__.status.get_outgoing_transitions(self.status)

    def get_available_transitions(self, user) -> List[fsm.Transition]:
        return self.__class__.status.get_available_transitions(self, self.status, user)
