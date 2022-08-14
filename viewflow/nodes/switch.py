from copy import copy

from .. import Gateway, Edge, ThisObject, mixins
from ..activation import Activation, AbstractGateActivation
from ..exceptions import FlowRuntimeError


class SwitchActivation(AbstractGateActivation):
    """Switch gateway activation."""

    def __init__(self, **kwargs):  # noqa D102
        self.next_task = None
        super().__init__(**kwargs)

    def calculate_next(self):
        """Calculate node to activate."""
        for node, cond in self.flow_task._branches:
            if cond:
                if cond(self):
                    self.next_task = node
                    break
            else:
                self.next_task = node

        if not self.next_task:
            raise FlowRuntimeError(f'No next task available for {self.flow_task.name}')

    @Activation.status.super()
    def activate_next(self):
        """Activate calculated node."""
        self.next_task.activate(prev_activation=self, token=self.task.token)


class Switch(mixins.TaskDescriptionMixin,
             mixins.DetailViewMixin,
             mixins.UndoViewMixin,
             mixins.CancelViewMixin,
             mixins.PerformViewMixin,
             Gateway):
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

    task_type = 'SWITCH'
    activation_class = SwitchActivation

    def __init__(self, **kwargs):  # noqa D102
        super().__init__(**kwargs)
        self._activate_next = []

    def _outgoing(self):
        for next_node, cond in self._activate_next:
            edge_class = 'cond_true' if cond else 'default'
            yield Edge(src=self, dst=next_node, edge_class=edge_class)

    def _resolve(self, resolver):
        self._activate_next = \
            [(resolver.get_implementation(node), cond)
             for node, cond in self._activate_next]
    
    def ready(self):
        next_nodes = []

        for node, condition in self._activate_next:
            if isinstance(condition, ThisObject):
                condition = getattr(self.flow_class.instance, condition.name)
            next_nodes.append((node, condition))
        self._activate_next = next_nodes
    
    @property
    def _branches(self):
        return self._activate_next

    def Case(self, node, cond=None):
        """Node to activate if condition is True.

        :param cond: Calable[activation] -> bool
        """
        result = copy(self)
        result._activate_next.append((node, cond))
        return result

    def Default(self, node):
        """Last node to activate if no one other succeed."""
        result = copy(self)
        result._activate_next.append((node, None))
        return result
