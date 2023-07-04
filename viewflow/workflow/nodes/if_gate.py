from viewflow import this

from ..base import Node, Edge
from ..activation import Activation
from . import mixins


class IfActivation(Activation):
    """Conditionally activate one of outgoing nodes."""

    _condition_result = None

    @Activation.status.super()
    def activate(self):
        self._condition_result = self.flow_task.condition(self)

    @Activation.status.super()
    def create_next(self):
        next_node = (
            self.flow_task._on_true
            if self._condition_result
            else self.flow_task._on_false
        )
        if next_node:
            yield next_node._create(self, self.task.token)


class If(Node):
    """If gateway, activate one of outgoing node."""

    activation_class = IfActivation

    task_type = "EXCLUSIVE_GATEWAY"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <path class="gateway" d="M25,0L50,25L25,50L0,25L25,0"/>
            <text class="gateway-marker" font-size="16px" x="25" y="31">X</text>
        """,
    }

    bpmn_element = "exclusiveGateway"

    def __init__(self, cond, **kwargs):
        super().__init__(**kwargs)
        self._condition = cond
        self._on_true = None
        self._on_false = None

    def _outgoing(self):
        yield Edge(src=self, dst=self._on_true, edge_class="cond_true")
        yield Edge(src=self, dst=self._on_false, edge_class="cond_false")

    def _resolve(self, instance):
        super()._resolve(instance)
        self._on_true = this.resolve(instance, self._on_true)
        self._on_false = this.resolve(instance, self._on_false)

    @property
    def condition(self):
        return this.resolve(self.flow_class.instance, self._condition)

    def Then(self, node):
        """Node activated if condition is True."""
        self._on_true = node
        return self

    def Else(self, node):
        """Node activated if condition is False."""
        self._on_false = node
        return self
