from django.db import transaction
from django.utils.timezone import now

from .. import lock
from ..base import Node
from ..activation import (
    Activation,
    process_not_cancelled,
    has_manage_permission,
    _can_cancel,
)
from ..exceptions import FlowRuntimeError
from ..status import STATUS, PROCESS
from ..signals import task_started, task_finished, task_failed, flow_finished


class EndActivation(Activation):
    """Activation that finishes the flow process."""

    @Activation.status.transition(
        source=STATUS.DONE,
        target=STATUS.CANCELED,
        conditions=[process_not_cancelled],
        permission=has_manage_permission,
    )
    def undo(self):
        self.process.finished = None
        self.process.status = PROCESS.NEW
        self.process.save()
        super().undo.original()

    @Activation.status.super()
    def activate(self):
        """
        Finalize the flow. If there is no active task, process marked as finished.
        """
        with self.exception_guard(), transaction.atomic(savepoint=True):
            self.task.started = now()
            task_started.send(
                sender=self.flow_class, process=self.process, task=self.task
            )

            active_tasks_count = (
                self.flow_class.task_class._default_manager.filter(
                    process=self.process, finished__isnull=True
                ).exclude(pk=self.task.pk)
            ).count()

            if active_tasks_count == 0:
                self.process.status = STATUS.DONE
                self.process.finished = now()
                self.process.save()

            task_finished.send(
                sender=self.flow_class, process=self.process, task=self.task
            )
            if active_tasks_count == 0:
                flow_finished.send(
                    sender=self.flow_class, process=self.process, task=self.task
                )

    @Activation.status.super()
    def create_next(self):
        """Do nothing"""
        return []

    @Activation.status.transition(
        source=[STATUS.ERROR],
        target=STATUS.CANCELED,
        permission=has_manage_permission,
    )
    def cancel(self):
        self.task.finished = now()
        self.task.save()


class End(Node):
    """
    End of the flow.

    If no other parallel activities exists, finishes the whole
    process.
    """

    activation_class = EndActivation

    task_type = "END"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event end-event" cx="25" cy="25" r="25"/>
        """,
    }

    bpmn_element = "endEvent"

    def _outgoing(self):
        return iter([])


def _cancel_active_tasks(activation):
    """Cancel every still-active task of the process, except the caller's."""
    active_tasks = activation.process.task_set.exclude(
        status__in=[STATUS.DONE, STATUS.CANCELED, STATUS.REVIVED, STATUS.ERROR]
    ).exclude(pk=activation.task.pk)

    activations = [task.flow_task.activation_class(task) for task in active_tasks]

    not_cancellable = [act for act in activations if not _can_cancel(act)]
    if not_cancellable:
        raise FlowRuntimeError(
            "Can't cancel {}".format(",".join(str(act.task) for act in not_cancellable))
        )

    for act in activations:
        act.cancel()


class TerminateEndActivation(EndActivation):
    """Finish the process, canceling every other active task."""

    @Activation.status.super()
    def activate(self):
        with self.exception_guard(), transaction.atomic(savepoint=True):
            self.task.started = now()
            task_started.send(
                sender=self.flow_class, process=self.process, task=self.task
            )

            _cancel_active_tasks(self)

            self.process.status = STATUS.DONE
            self.process.finished = now()
            self.process.save()

            task_finished.send(
                sender=self.flow_class, process=self.process, task=self.task
            )
            flow_finished.send(
                sender=self.flow_class, process=self.process, task=self.task
            )


class TerminateEnd(End):
    """
    Terminate end event: immediately cancels all other active tasks and
    finishes the process, without waiting for parallel branches.
    """

    activation_class = TerminateEndActivation

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event end-event" cx="25" cy="25" r="25"/>
            <circle cx="25" cy="25" r="14" fill="rgb(0, 0, 0)"/>
        """,
    }

    def bpmn_content(self):
        return "<bpmn:terminateEventDefinition/>"


def _fail_parent_task(parent_task, code):
    """Mark the parent subprocess task as failed with the child's error."""
    with parent_task.activation() as activation:
        task = activation.task
        if task.status in (
            STATUS.DONE,
            STATUS.CANCELED,
            STATUS.REVIVED,
            STATUS.ERROR,
        ):
            return
        if not task.data:
            task.data = {}
        task.data["_exception"] = {
            "title": f"Subprocess failed with error {code!r}",
            "code": code,
        }
        task.finished = now()
        activation._set_status(STATUS.ERROR)
        task.save()
        task_failed.send(
            sender=activation.flow_class, process=activation.process, task=task
        )


class ErrorEndActivation(EndActivation):
    """Finish the process as failed, propagating the error to a parent."""

    @Activation.status.super()
    def activate(self):
        with self.exception_guard(), transaction.atomic(savepoint=True):
            self.task.started = now()
            task_started.send(
                sender=self.flow_class, process=self.process, task=self.task
            )

            _cancel_active_tasks(self)

            code = self.flow_task._code
            self.process.status = STATUS.DONE
            self.process.finished = now()
            if hasattr(self.process, "data"):
                if not self.process.data:
                    self.process.data = {}
                self.process.data["_error"] = {"code": code}
            self.process.save()

            task_finished.send(
                sender=self.flow_class, process=self.process, task=self.task
            )

            # deliberately no flow_finished: a failed end must not complete
            # the parent subprocess task normally; instead the parent task
            # is marked ERROR under its own lock, firing its ErrorBoundary
            parent_task = self.process.parent_task
            if parent_task is not None:
                lock.after_lock_released(lambda: _fail_parent_task(parent_task, code))


class ErrorEnd(End):
    """
    Error end event: interrupts the process and records it as failed.

    Inside a subprocess, the parent ``Subprocess`` task is marked ``ERROR``
    with the given code, so the parent's ``.OnError`` boundary can catch
    it. The error code is stored in ``process.data["_error"]``.

    Example::

        fail_end = flow.ErrorEnd("payment-failed")

    """

    activation_class = ErrorEndActivation

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event end-event" cx="25" cy="25" r="25"/>
            <path d="M 20 36 L 27 22 L 22 24 L 30 13 L 28 22 L 33 20 Z" fill="none" stroke="rgb(0, 0, 0)" stroke-miterlimit="10"/>
        """,
    }

    def __init__(self, code=None, **kwargs):
        super().__init__(**kwargs)
        self._code = code

    def bpmn_content(self):
        return "<bpmn:errorEventDefinition/>"
