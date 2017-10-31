from copy import copy

from .. import Gateway, Edge, mixins
from ..activation import Activation, AbstractGateActivation
from ..exceptions import FlowRuntimeError
from ..token import Token
from .join import Join


class SplitActivation(AbstractGateActivation):
    """Parallel split gateway activation."""

    def __init__(self, **kwargs):   # noqa D102
        self.next_tasks = []
        super(SplitActivation, self).__init__(**kwargs)

    def calculate_next(self):
        """Calculate nodes list to activate."""
        for node, cond in self.flow_task._branches:
            if cond:
                if cond(self):
                    self.next_tasks.append(node)
            else:
                self.next_tasks.append(node)

        if not self.next_tasks:
            raise FlowRuntimeError('No next task available for {}'.format(self.flow_task.name))

    @Activation.status.super()
    def activate_next(self):
        """Activate next tasks for parallel execution.

        Each task would have a new execution token attached,
        the Split task token as a common prefix.
        """
        token_source = Token.split_token_source(self.task.token, self.task.pk)

        next_tasks = (
            [task for task in self.next_tasks if not isinstance(task, Join)] +
            [task for task in self.next_tasks if isinstance(task, Join)]
        )

        for n, next_task in enumerate(next_tasks, 1):
            next_task.activate(prev_activation=self, token=next(token_source))


class Split(mixins.TaskDescriptionMixin,
            mixins.DetailViewMixin,
            mixins.UndoViewMixin,
            mixins.CancelViewMixin,
            mixins.PerformViewMixin,
            Gateway):
    """Parallel split gateway.

    Activates outgoing tasks to execute concurrently. Assumes that all
    outgoing path converges at the same Join node.

    If Split has no nodes to activate, FlowRuntimeError would be
    raised.

    Example::

        split_clerk_warehouse = (
            flow.Split()
            .Next(
                this.package_goods,
                cond=lambda a: a.process.need_packaging)
            .Always(this.shipment_type)
        )
    """

    task_type = 'SPLIT'
    activation_class = SplitActivation

    def __init__(self, **kwargs):   # noqa D102
        super(Split, self).__init__(**kwargs)
        self._activate_next = []

    def _outgoing(self):
        for next_node, cond in self._activate_next:
            edge_class = 'cond_true' if cond else 'default'
            yield Edge(src=self, dst=next_node, edge_class=edge_class)

    def _resolve(self, resolver):
        self._activate_next = \
            [(resolver.get_implementation(node), cond)
             for node, cond in self._activate_next]

    @property
    def _branches(self):
        return self._activate_next

    def Next(self, node, cond=None):
        """Node to activate if condition is true.

        :param cond: Callable[activation] -> bool

        """
        result = copy(self)
        result._activate_next.append((node, cond))
        return result

    def Always(self, node):
        """Activate that node unconditionally.

        Shortcut for `.Next` without a condition
        """
        result = copy(self)
        result._activate_next.append((node, None))
        return result
