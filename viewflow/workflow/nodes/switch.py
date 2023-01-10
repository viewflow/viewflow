from django.utils.timezone import now

from viewflow import this
from viewflow.workflow.base import Node, Edge
from viewflow.workflow.exceptions import FlowRuntimeError
from viewflow.workflow.activation import Activation

from . import mixins
from ..status import STATUS


class SwitchActivation(Activation):
    """Switch gateway activation."""

    next_task = None

    @Activation.status.super()
    def activate(self):
        for node, cond in self.flow_task._branches:
            if cond:
                if cond(self):
                    self.next_task = node
                    break
            else:
                self.next_task = node

        if not self.next_task:
            raise FlowRuntimeError(
                "No next task available for {}".format(self.flow_task.name)
            )

    @Activation.status.super()
    def create_next(self):
        yield self.next_task._create(self, self.task.token)


class Switch(Node):
    """
    Gateway that selects one of the outgoing node.

    Activates first node with matched condition.

    Example::

        select_responsible_person = (
            flow.Switch()
            .Case(this.dean_approval, lambda act: a.process.need_dean)
            .Case(this.head_approval, lambda act: a.process.need_head)
            .Default(this.supervisor_approval)
        )

    """

    task_type = "SWITCH"
    activation_class = SwitchActivation

    def __init__(self, **kwargs):  # noqa D102
        super(Switch, self).__init__(**kwargs)
        self._activate_next = []

    def _outgoing(self):
        for next_node, cond in self._activate_next:
            edge_class = "cond_true" if cond else "default"
            yield Edge(src=self, dst=next_node, edge_class=edge_class)

    def _resolve(self, instance):
        super()._resolve(instance)

        next_nodes = []
        for node, condition in self._activate_next:
            node = this.resolve(instance, node)
            condition = this.resolve(instance, condition)
            next_nodes.append((node, condition))
        self._activate_next = next_nodes

    @property
    def _branches(self):
        return self._activate_next

    def Case(self, node, cond=None):
        """Node to activate if condition is True.

        :param cond: Calable[activation] -> bool
        """
        self._activate_next.append((node, cond))
        return self

    def Default(self, node):
        """Last node to activate if no one other succeed."""
        self._activate_next.append((node, None))
        return self
