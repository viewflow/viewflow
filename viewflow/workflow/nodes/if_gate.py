from django.db import transaction
from django.utils.timezone import now
from viewflow import this

from ..base import Node, Edge
from ..activation import Activation, has_manage_permission
from ..status import STATUS
from . import mixins


class IfActivation(Activation):
    """Conditionally activate one of outgoing nodes."""

    _condition_result = None

    @Activation.status.super()
    def activate(self):
        with transaction.atomic(savepoint=True), self.exception_guard():
            self._condition_result = self.flow_task._condition(self)

    @Activation.status.super()
    def create_next(self):
        next_node, next_data_source, next_seed_sourse = (
            (
                self.flow_task._on_true,
                self.flow_task._on_true_data,
                self.flow_task._on_true_seed,
            )
            if self._condition_result
            else (
                self.flow_task._on_false,
                self.flow_task._on_false_data,
                self.flow_task._on_false_seed,
            )
        )
        if next_node:
            next_data = next_data_source(self) if next_data_source else None
            next_seed = next_seed_sourse(self) if next_seed_sourse else None
            yield next_node._create(
                self, self.task.token, data=next_data, seed=next_seed
            )

    @Activation.status.transition(
        source=[STATUS.ERROR],
        target=STATUS.CANCELED,
        permission=has_manage_permission,
    )
    def cancel(self):
        self.task.finished = now()
        self.task.save()


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
        self._on_true_data = None
        self._on_true_seed = None
        self._on_false = None
        self._on_false_data = None
        self._on_false_seed = None

    def _outgoing(self):
        yield Edge(src=self, dst=self._on_true, edge_class="cond_true")
        yield Edge(src=self, dst=self._on_false, edge_class="cond_false")

    def _resolve(self, instance):
        super()._resolve(instance)

        self._condition = this.resolve(self.flow_class.instance, self._condition)
        self._on_true = this.resolve(instance, self._on_true)
        self._on_true_data = this.resolve(instance, self._on_true_data)
        self._on_true_seed = this.resolve(instance, self._on_true_seed)

        self._on_false = this.resolve(instance, self._on_false)
        self._on_false_data = this.resolve(instance, self._on_false_data)
        self._on_false_seed = this.resolve(instance, self._on_false_seed)

    def Then(self, node, task_data=None, task_seed=None):
        """Node activated if condition is True."""
        self._on_true = node
        self._on_true_data = task_data
        self._on_true_seed = task_seed
        return self

    def Else(self, node, task_data=None, task_seed=None):
        """Node activated if condition is False."""
        self._on_false = node
        self._on_false_data = task_data
        self._on_false_seed = task_seed
        return self
