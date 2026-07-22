from django.db import transaction
from django.utils.timezone import now

from viewflow import this
from ..activation import Activation, has_manage_permission
from ..base import Node
from ..status import STATUS
from ..signals import task_started
from . import mixins


class FunctionActivation(mixins.NextNodeActivationMixin, Activation):
    """
    Handle  Activation.

    Executes a callback immediately.
    """

    @Activation.status.super()
    def activate(self):
        """Perform the callback within current exception propagation strategy."""
        with self.exception_guard(), transaction.atomic(savepoint=True):
            self.task.started = now()
            task_started.send(
                sender=self.flow_class, process=self.process, task=self.task
            )
            self.flow_task._func(self)

    @Activation.status.transition(
        source=[STATUS.ERROR],
        target=STATUS.CANCELED,
        permission=has_manage_permission,
    )
    def cancel(self):
        self.task.finished = now()
        self.task.save()


class Function(mixins.NextNodeMixin, mixins.NodePermissionMixin, Node):
    """
    Callback executed synchronously on a task activation.
    """

    activation_class = FunctionActivation

    task_type = "FUNCTION"

    shape = {
        "width": 150,
        "height": 100,
        "text-align": "middle",
        "svg": """
            <rect class="task" width="150" height="100" rx="5" ry="5"/>
            <path class="task-marker"
                  d="m 15,20 c 10,-6 -8,-8 3,-15 l -9,0 c -11,7 7,9 -3,15 z
                     m -7,-12 l 5,0 m -4.5,3 l 4.5,0 m -3,3 l 5,0 m -4,3 l 5,0"/>
        """,
    }

    bpmn_element = "scriptTask"

    def __init__(self, func, **kwargs):  # noqa D102
        super().__init__(**kwargs)
        self._func = func

    def _resolve(self, instance):
        super()._resolve(instance)
        self._func = this.resolve(instance, self._func)


class SendHandle(Function):
    """
    Outbound message hook, executed synchronously (BPMN send task).

    Example::

        send = flow.SendHandle(this.notify_customer).Next(this.end)

    """

    bpmn_element = "sendTask"

    shape = {
        "width": 150,
        "height": 100,
        "text-align": "middle",
        "svg": """
            <rect class="task" width="150" height="100" rx="5" ry="5"/>
            <rect x="8" y="8" width="21" height="14" fill="rgb(0, 0, 0)" stroke="rgb(0, 0, 0)"/>
            <path d="M 8 8 L 18.5 16 L 29 8" fill="none" stroke="rgb(255, 255, 255)" stroke-width="1.5"/>
        """,
    }


class BusinessRule(Function):
    """
    Business rule evaluation, executed synchronously (BPMN business rule
    task).

    Example::

        discount = flow.BusinessRule(this.calc_discount).Next(this.end)

    """

    bpmn_element = "businessRuleTask"

    shape = {
        "width": 150,
        "height": 100,
        "text-align": "middle",
        "svg": """
            <rect class="task" width="150" height="100" rx="5" ry="5"/>
            <rect x="8" y="8" width="24" height="16" fill="none" stroke="rgb(0, 0, 0)"/>
            <path d="M 8 13 L 32 13 M 8 18.5 L 32 18.5 M 16 13 L 16 24" fill="none" stroke="rgb(0, 0, 0)"/>
        """,
    }
