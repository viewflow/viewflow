from copy import copy

from .. import Gateway, Edge, ThisObject, mixins
from ..activation import Activation, AbstractGateActivation


class IfActivation(AbstractGateActivation):
    """Conditionally activate one of outgoing nodes."""

    def __init__(self, **kwargs):  # noqa D102
        self.condition_result = None
        super(IfActivation, self).__init__(**kwargs)

    def calculate_next(self):
        """Calculate node to activate."""
        self.condition_result = self.flow_task.condition(self)

    @Activation.status.super()
    def activate_next(self):
        """Conditionally activate one of outgoing nodes."""
        if self.condition_result:
            self.flow_task._on_true.activate(prev_activation=self, token=self.task.token)
        else:
            self.flow_task._on_false.activate(prev_activation=self, token=self.task.token)


class If(mixins.TaskDescriptionMixin,
         mixins.DetailViewMixin,
         mixins.UndoViewMixin,
         mixins.CancelViewMixin,
         mixins.PerformViewMixin,
         Gateway):
    """If gateway, activate one of outgoing node.

    Example::

        class MyFlow(Flow):
            check_approve = (
                flow.If(lambda activation: activation.process.is_approved)
                .Then(this.send_message)
                .Else(this.end_rejected)
            )
    """

    task_type = 'IF'
    activation_class = IfActivation

    def __init__(self, cond, **kwargs):
        """
        Instantiate If gate node.

        :param cond: Callable[activation] -> bool
        """
        super(If, self).__init__(**kwargs)
        self._condition = cond
        self._on_true = None
        self._on_false = None

    def _outgoing(self):
        yield Edge(src=self, dst=self._on_true, edge_class='cond_true')
        yield Edge(src=self, dst=self._on_false, edge_class='cond_false')

    def _resolve(self, resolver):
        self._on_true = resolver.get_implementation(self._on_true)
        self._on_false = resolver.get_implementation(self._on_false)

    def ready(self):
        if isinstance(self._condition, ThisObject):
            self._condition = getattr(self.flow_class.instance, self._condition.name)

    def Then(self, node):
        """Node activated if condition is True."""
        result = copy(self)
        result._on_true = node
        return result

    def Else(self, node):
        """Node activated if condition is False."""
        result = copy(self)
        result._on_false = node
        return result

    @property
    def condition(self):  # noqa D012
        return self._condition
