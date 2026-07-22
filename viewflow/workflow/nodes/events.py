"""Intermediate catch and throw events.

Single-process semantics: throw events deliver to catch events at runtime;
no collaboration diagrams are drawn.
"""

import logging

from django.db import transaction
from django.utils.timezone import now

from viewflow import this

from .. import lock
from ..activation import Activation
from ..base import Node
from ..context import Context
from ..exceptions import FlowLockFailed
from ..signals import task_started
from ..status import STATUS
from . import mixins
from .func import Function, FunctionActivation
from .handle import Handle

logger = logging.getLogger(__name__)


class MessageCatch(Handle):
    """
    Intermediate message catch event, completed from external code.

    Same calling convention as ``flow.Handle``, exported as a BPMN message
    catch event::

        wait_payment = flow.MessageCatch(this.on_payment).Next(this.ship)

        # from external code
        task = process.task_set.get(flow_task=MyFlow.wait_payment, status=STATUS.NEW)
        MyFlow.wait_payment.run(task, amount=100)

    """

    task_type = "EVENT"
    bpmn_element = "intermediateCatchEvent"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event" cx="25" cy="25" r="25"/>
            <ellipse cx="25" cy="25" rx="19.5" ry="19.5" fill="rgb(255, 255, 255)" stroke="rgb(0, 0, 0)"/>
            <rect x="15" y="18" width="20" height="14" fill="none" stroke="rgb(0, 0, 0)"/>
            <path d="M 15 18 L 25 27 L 35 18" fill="none" stroke="rgb(0, 0, 0)"/>
        """,
    }

    def bpmn_content(self):
        return "<bpmn:messageEventDefinition/>"


def broadcast_signal(name, flows=None):
    """Fire every armed ``flow.SignalCatch`` with a matching signal name.

    Returns the number of catch tasks delivered to. By default discovers
    flows by importing every installed app's ``flows`` module; pass ``flows``
    to restrict the broadcast. Each catch task is fired under its own flow
    lock, so a task locked by another worker is skipped until the next throw.
    """
    from ..base import Flow
    from ..checks import _all_flow_subclasses

    if flows is None:
        from django.utils.module_loading import autodiscover_modules

        autodiscover_modules("flows")
        flows = _all_flow_subclasses(Flow)

    delivered = 0
    for flow_class in flows:
        catch_nodes = [
            node
            for node in flow_class.instance.nodes()
            if isinstance(node, SignalCatch) and node._signal_name == name
        ]
        for node in catch_nodes:
            armed = flow_class.task_class._default_manager.filter(
                flow_task=node, status=STATUS.NEW
            )
            for task in armed:
                try:
                    with task.activation() as activation:
                        if activation.start.can_proceed():
                            activation.start()
                            activation.execute()
                            delivered += 1
                except FlowLockFailed:
                    logger.info("Signal catch task %s is locked, skipped", task.pk)
                except Exception:  # one broken flow must not stop delivery
                    logger.exception("Signal catch task %s failed to fire", task.pk)

    return delivered


class SignalCatchActivation(mixins.NextNodeActivationMixin, Activation):
    """Stays armed at NEW until a matching signal is broadcast."""

    @Activation.status.super()
    def activate(self):
        """Do nothing -- wait for the signal."""

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def start(self):
        self.task.started = now()
        self.task.save()

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.DONE)
    def complete(self):
        super().complete.original()

    @Activation.status.transition(source=STATUS.STARTED)
    def execute(self):
        """Fire the caught signal and continue.

        Runs from the broadcast dispatcher, so a downstream failure is
        recorded as a task ERROR instead of propagating into the sweep.
        """
        self.complete()
        with Context(propagate_exception=False):
            self.activate_next()

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.CANCELED)
    def cancel(self):
        self.task.finished = now()
        self.task.save()


class SignalCatch(mixins.NextNodeMixin, Node):
    """
    Intermediate signal catch event.

    Waits until a matching signal is thrown by any process. A single throw
    releases every armed catch with the same name, across processes and flow
    classes::

        wait = flow.SignalCatch("order-shipped").Next(this.notify)

    """

    task_type = "EVENT"
    activation_class = SignalCatchActivation
    bpmn_element = "intermediateCatchEvent"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event" cx="25" cy="25" r="25"/>
            <ellipse cx="25" cy="25" rx="19.5" ry="19.5" fill="rgb(255, 255, 255)" stroke="rgb(0, 0, 0)"/>
            <path d="M 25 12 L 35 30 L 15 30 Z" fill="none" stroke="rgb(0, 0, 0)"/>
        """,
    }

    def __init__(self, name, **kwargs):
        super().__init__(**kwargs)
        self._signal_name = name

    def bpmn_content(self):
        return "<bpmn:signalEventDefinition/>"


class SignalThrowActivation(FunctionActivation):
    """Broadcast the signal once the throwing process's lock is released."""

    @Activation.status.super()
    def activate(self):
        with self.exception_guard(), transaction.atomic(savepoint=True):
            self.task.started = now()
            task_started.send(
                sender=self.flow_class, process=self.process, task=self.task
            )
            name = self.flow_task._signal_name
            # deferring past the current lock avoids re-entering this
            # process's lock (self-catch) and taking a second process's
            # lock nested inside this one
            lock.after_lock_released(lambda: broadcast_signal(name))


class SignalThrow(mixins.NextNodeMixin, Node):
    """
    Intermediate signal throw event.

    Broadcasts a named signal to every armed ``flow.SignalCatch``, then
    continues::

        fire = flow.SignalThrow("order-shipped").Next(this.end)

    """

    task_type = "EVENT"
    activation_class = SignalThrowActivation
    bpmn_element = "intermediateThrowEvent"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event" cx="25" cy="25" r="25"/>
            <ellipse cx="25" cy="25" rx="19.5" ry="19.5" fill="rgb(255, 255, 255)" stroke="rgb(0, 0, 0)"/>
            <path d="M 25 12 L 35 30 L 15 30 Z" fill="rgb(0, 0, 0)" stroke="rgb(0, 0, 0)"/>
        """,
    }

    def __init__(self, name, **kwargs):
        super().__init__(**kwargs)
        self._signal_name = name

    def bpmn_content(self):
        return "<bpmn:signalEventDefinition/>"


class ConditionalCatchActivation(mixins.NextNodeActivationMixin, Activation):
    """Stays armed at NEW until its condition over process data holds."""

    @Activation.status.super()
    def activate(self):
        """Do nothing -- wait for the condition."""

    def condition_met(self):
        return bool(self.flow_task._condition(self))

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def start(self):
        self.task.started = now()
        self.task.save()

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.DONE)
    def complete(self):
        super().complete.original()

    @Activation.status.transition(source=STATUS.STARTED)
    def execute(self):
        """Fire and continue -- runs from the dispatcher, so a downstream
        failure is recorded as a task ERROR rather than breaking the sweep."""
        self.complete()
        with Context(propagate_exception=False):
            self.activate_next()

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.CANCELED)
    def cancel(self):
        self.task.finished = now()
        self.task.save()


class ConditionalCatch(mixins.NextNodeMixin, Node):
    """
    Intermediate conditional catch event.

    Waits until a condition over the process data becomes true. The condition
    is evaluated by the periodic ``workflow_timers`` dispatcher, the same
    sweep that fires durable timers::

        wait = flow.ConditionalCatch(
            lambda activation: activation.process.approved
        ).Next(this.proceed)

    :param condition: a callable ``activation -> bool``.
    """

    task_type = "CONDITION"
    activation_class = ConditionalCatchActivation
    bpmn_element = "intermediateCatchEvent"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event" cx="25" cy="25" r="25"/>
            <ellipse cx="25" cy="25" rx="19.5" ry="19.5" fill="rgb(255, 255, 255)" stroke="rgb(0, 0, 0)"/>
            <rect x="16" y="14" width="18" height="22" fill="none" stroke="rgb(0, 0, 0)"/>
            <path d="M 19 20 L 31 20 M 19 25 L 31 25 M 19 30 L 27 30" fill="none" stroke="rgb(0, 0, 0)"/>
        """,
    }

    def __init__(self, condition, **kwargs):
        super().__init__(**kwargs)
        self._condition = condition

    def _resolve(self, instance):
        super()._resolve(instance)
        self._condition = this.resolve(instance, self._condition)

    def bpmn_content(self):
        # the executable condition lives in Python; the export carries an
        # empty formal expression as the BPMN placeholder
        return (
            "<bpmn:conditionalEventDefinition>"
            '<bpmn:condition xsi:type="bpmn:tFormalExpression"/>'
            "</bpmn:conditionalEventDefinition>"
        )


class MessageThrow(Function):
    """
    Intermediate message throw event -- an outbound hook executed
    synchronously when the previous task finishes::

        notify = flow.MessageThrow(this.send_receipt).Next(this.end)

    """

    task_type = "EVENT"
    bpmn_element = "intermediateThrowEvent"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event" cx="25" cy="25" r="25"/>
            <ellipse cx="25" cy="25" rx="19.5" ry="19.5" fill="rgb(255, 255, 255)" stroke="rgb(0, 0, 0)"/>
            <rect x="15" y="18" width="20" height="14" fill="rgb(0, 0, 0)" stroke="rgb(0, 0, 0)"/>
            <path d="M 15 18 L 25 27 L 35 18" fill="none" stroke="rgb(255, 255, 255)" stroke-width="1.5"/>
        """,
    }

    def bpmn_content(self):
        return "<bpmn:messageEventDefinition/>"
