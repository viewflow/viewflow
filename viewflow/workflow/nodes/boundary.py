"""Boundary events -- catch events attached to the border of a host task.

A boundary node is armed (its task row created) together with every task of
its host node, and canceled when that host task finishes. An interrupting
boundary cancels the host when it fires; a non-interrupting one leaves the
host running and activates a parallel path.
"""

import logging

from django.db import transaction
from django.utils.timezone import now

from viewflow import this

from .. import lock
from ..activation import Activation
from ..base import Edge, Node
from ..exceptions import FlowLockFailed
from ..signals import task_failed, task_finished, task_started
from ..status import STATUS
from . import mixins
from .func import FunctionActivation
from .timer import Timer, TimerActivation

logger = logging.getLogger(__name__)


class BoundaryEventMixin:
    """Common node machinery for events attached to a host task."""

    bpmn_element = "boundaryEvent"

    def __init__(self, attached_to, *args, interrupting=True, **kwargs):
        super().__init__(*args, **kwargs)
        self._attached_to = attached_to
        self._interrupting = interrupting

    def _resolve(self, instance):
        super()._resolve(instance)
        self._attached_to = this.resolve(instance, self._attached_to)

    def _ready(self):
        super()._ready()
        self._attached_to._boundary_events.append(self)
        task_finished.connect(self._on_host_finished, sender=self.flow_class)

    def _incoming(self):
        # a synthetic edge places the boundary next to its host on the
        # chart; it is not a BPMN sequence flow and is dropped from exports
        yield from super()._incoming()
        yield Edge(src=self._attached_to, dst=self, edge_class="boundary")

    def _arm(self, host_activation):
        """Create and activate the boundary task alongside the host task."""
        activation = self.activation_class.create(
            self, host_activation, host_activation.task.token
        )
        activation.activate()

    def _on_host_finished(self, **signal_kwargs):
        host_task = signal_kwargs["task"]
        if host_task.flow_task != self._attached_to:
            return
        armed = self.flow_class.task_class._default_manager.filter(
            flow_task=self,
            process=host_task.process,
            previous=host_task,
        ).exclude(
            status__in=[STATUS.DONE, STATUS.CANCELED, STATUS.REVIVED, STATUS.ERROR]
        )
        for task in armed:
            activation = self.activation_class(task)
            if activation.cancel.can_proceed():
                activation.cancel()

    def bpmn_attrs(self):
        return {
            "attachedToRef": f"id_node_{self._attached_to.name}",
            "cancelActivity": "true" if self._interrupting else "false",
        }


class BoundaryActivationMixin:
    def cancel_host_tasks(self):
        """Cancel still-active host tasks of an interrupting boundary."""
        active = self.task.previous.exclude(
            status__in=[STATUS.DONE, STATUS.CANCELED, STATUS.REVIVED]
        )
        for host_task in active:
            activation = host_task.flow_task.activation_class(host_task)
            if activation.cancel.can_proceed():
                activation.cancel()
            else:
                logger.warning(
                    "Boundary event %s could not cancel host task %s in state %s",
                    self.flow_task.name,
                    host_task.pk,
                    host_task.status,
                )


class TimerBoundaryActivation(BoundaryActivationMixin, TimerActivation):
    @Activation.status.transition(source=STATUS.STARTED)
    def execute(self):
        if self.flow_task._interrupting:
            self.cancel_host_tasks()
        super().execute.original()


class TimerBoundary(BoundaryEventMixin, Timer):
    """
    Timer attached to a task: fires when the delay elapses before the host
    task completes.

    Fired by the same ``workflow_timers`` dispatcher as ``flow.Timer``.
    Interrupting (default) cancels the host task; ``interrupting=False``
    leaves the host running and starts a parallel path.

    Example::

        approve = (
            flow.View(...)
            .OnTimeout(timedelta(days=3), this.escalate)
            .Next(this.end)
        )

    """

    activation_class = TimerBoundaryActivation

    # smaller than a standalone flow.Timer, with an opaque backing so the host
    # task border does not show through -- boundary events sit on that border
    shape = {
        "width": 36,
        "height": 36,
        "svg": """
            <g transform="scale(0.72)">
            <circle cx="25" cy="25" r="25" fill="rgb(255, 255, 255)" stroke="none"/>
            <ellipse cx="25" cy="25" rx="19.5" ry="19.5" fill="rgb(255, 255, 255)" stroke="rgb(0, 0, 0)"/>
            <path d="M 25 5.5 L 25 8 M 34.69 8.05 L 33.29 10.5 M 41.77 15.14 L 39.32 16.63 M 44.5 25 L 41.92 25 M 41.77 34.79 L 39.32 33.29 M 34.69 41.87 L 33.29 39.43 M 25 41.92 L 25 44.5 M 15.23 41.87 L 16.63 39.43 M 8.15 34.79 L 10.6 33.29 M 5.5 25 L 8 25 M 8.15 15.14 L 10.6 16.63 M 15.23 8.05 L 16.63 10.5 M 25.96 8.25 L 25 25 L 35.94 25.46" fill="none" stroke="rgb(0, 0, 0)" stroke-miterlimit="10"/>
            <circle class="event" cx="25" cy="25" r="25"/>
            </g>
        """,
    }


class ErrorBoundaryActivation(
    BoundaryActivationMixin, mixins.NextNodeActivationMixin, Activation
):
    @Activation.status.super()
    def activate(self):
        """Stay armed until the host task fails."""

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def start(self):
        self.task.started = now()
        self.task.save()

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.DONE)
    def complete(self):
        super().complete.original()

    @Activation.status.transition(source=STATUS.STARTED)
    def execute(self):
        if self.flow_task._interrupting:
            self.cancel_host_tasks()
        self.complete()
        self.activate_next()

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.CANCELED)
    def cancel(self):
        self.task.finished = now()
        self.task.save()


class ErrorBoundary(BoundaryEventMixin, mixins.NextNodeMixin, Node):
    """
    Catch a host task failure and route it to a recovery path.

    Fires when the host task is marked ``ERROR`` -- a failure recorded in a
    background context (job, timer, function). Interrupting (default) also
    cancels the errored host task.

    Example::

        deploy = flow.Function(this.run_deploy).OnError(this.rollback).Next(this.end)

    """

    task_type = "EVENT"
    activation_class = ErrorBoundaryActivation

    def __init__(self, attached_to, code=None, **kwargs):
        super().__init__(attached_to, **kwargs)
        self._code = code

    shape = {
        "width": 36,
        "height": 36,
        "svg": """
            <g transform="scale(0.72)">
            <circle cx="25" cy="25" r="25" fill="rgb(255, 255, 255)" stroke="none"/>
            <circle class="event" cx="25" cy="25" r="25"/>
            <ellipse cx="25" cy="25" rx="19.5" ry="19.5" fill="rgb(255, 255, 255)" stroke="rgb(0, 0, 0)"/>
            <path d="M 20 36 L 27 22 L 22 24 L 30 13 L 28 22 L 33 20 Z" fill="none" stroke="rgb(0, 0, 0)" stroke-miterlimit="10"/>
            </g>
        """,
    }

    def _ready(self):
        super()._ready()
        task_failed.connect(self._on_host_failed, sender=self.flow_class)

    def _on_host_failed(self, **signal_kwargs):
        host_task = signal_kwargs["task"]
        if host_task.flow_task != self._attached_to:
            return
        if self._code is not None:
            exception = (host_task.data or {}).get("_exception", {})
            if exception.get("code") != self._code:
                return
        armed = self.flow_class.task_class._default_manager.filter(
            flow_task=self,
            process=host_task.process,
            previous=host_task,
            status=STATUS.NEW,
        )
        for task in armed:
            activation = self.activation_class(task)
            activation.start()
            activation.execute()

    def bpmn_content(self):
        return "<bpmn:errorEventDefinition/>"


def _fire_escalation_boundary(parent_task, code):
    """Fire the parent subprocess's matching escalation boundary, if armed."""
    host_node = parent_task.flow_task
    flow_class = host_node.flow_class
    for node in flow_class.instance.nodes():
        if not isinstance(node, EscalationBoundary):
            continue
        if node._attached_to != host_node:
            continue
        if node._code is not None and node._code != code:
            continue
        armed = flow_class.task_class._default_manager.filter(
            flow_task=node,
            process=parent_task.process,
            previous=parent_task,
            status=STATUS.NEW,
        )
        for task in armed:
            try:
                with task.activation() as activation:
                    if activation.start.can_proceed():
                        activation.start()
                        activation.execute()
            except FlowLockFailed:
                logger.info("Escalation boundary task %s is locked, skipped", task.pk)


class EscalationThrowActivation(FunctionActivation):
    """Notify the parent's escalation boundary without interrupting anything."""

    @Activation.status.super()
    def activate(self):
        with self.exception_guard(), transaction.atomic(savepoint=True):
            self.task.started = now()
            task_started.send(
                sender=self.flow_class, process=self.process, task=self.task
            )
            code = self.flow_task._code
            parent_task = self.process.parent_task
            if parent_task is not None:
                # defer past the child's lock: the boundary lives in the
                # parent process and firing it needs the parent lock, which
                # must not be taken nested inside the child's
                lock.after_lock_released(
                    lambda: _fire_escalation_boundary(parent_task, code)
                )


class EscalationThrow(mixins.NextNodeMixin, Node):
    """
    Escalation throw event: signals the parent process that something needs
    attention, then continues. Neither the child nor the parent subprocess is
    interrupted.

    Raised inside a subprocess and caught by the parent's ``.OnEscalation``
    boundary::

        over_budget = flow.EscalationThrow("over-budget").Next(this.keep_going)

    """

    task_type = "EVENT"
    activation_class = EscalationThrowActivation
    bpmn_element = "intermediateThrowEvent"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event" cx="25" cy="25" r="25"/>
            <ellipse cx="25" cy="25" rx="19.5" ry="19.5" fill="rgb(255, 255, 255)" stroke="rgb(0, 0, 0)"/>
            <path d="M 25 13 L 32 34 L 25 26 L 18 34 Z" fill="rgb(0, 0, 0)" stroke="rgb(0, 0, 0)"/>
        """,
    }

    def __init__(self, code=None, **kwargs):
        super().__init__(**kwargs)
        self._code = code

    def bpmn_content(self):
        return "<bpmn:escalationEventDefinition/>"


class EscalationBoundaryActivation(mixins.NextNodeActivationMixin, Activation):
    """Armed on a subprocess task, fired by a child's escalation throw."""

    @Activation.status.super()
    def activate(self):
        """Stay armed until an escalation is thrown."""

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def start(self):
        self.task.started = now()
        self.task.save()

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.DONE)
    def complete(self):
        super().complete.original()

    @Activation.status.transition(source=STATUS.STARTED)
    def execute(self):
        # escalation never cancels the host; the subprocess keeps running
        self.complete()
        self.activate_next()

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.CANCELED)
    def cancel(self):
        self.task.finished = now()
        self.task.save()


class EscalationBoundary(BoundaryEventMixin, mixins.NextNodeMixin, Node):
    """
    Catch an escalation thrown inside a subprocess and start a parallel path.

    Non-interrupting: the subprocess (and the child that threw the
    escalation) keep running.

    Example::

        sub = (
            flow.Subprocess(OrderFlow.start)
            .OnEscalation(this.notify_manager, code="over-budget")
            .Next(this.end)
        )

    """

    task_type = "EVENT"
    activation_class = EscalationBoundaryActivation

    shape = {
        "width": 36,
        "height": 36,
        "svg": """
            <g transform="scale(0.72)">
            <circle cx="25" cy="25" r="25" fill="rgb(255, 255, 255)" stroke="none"/>
            <circle class="event" cx="25" cy="25" r="25"/>
            <ellipse cx="25" cy="25" rx="19.5" ry="19.5" fill="rgb(255, 255, 255)" stroke="rgb(0, 0, 0)"/>
            <path d="M 25 13 L 32 34 L 25 26 L 18 34 Z" fill="none" stroke="rgb(0, 0, 0)"/>
            </g>
        """,
    }

    def __init__(self, attached_to, code=None, **kwargs):
        super().__init__(attached_to, interrupting=False, **kwargs)
        self._code = code

    def bpmn_content(self):
        return "<bpmn:escalationEventDefinition/>"
