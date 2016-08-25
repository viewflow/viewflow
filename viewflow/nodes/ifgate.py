from copy import copy

from .. import Gateway, Edge, mixins
from ..activation import AbstractGateActivation


class IfActivation(AbstractGateActivation):
    def __init__(self, **kwargs):
        self.condition_result = None
        super(IfActivation, self).__init__(**kwargs)

    def calculate_next(self):
        self.condition_result = self.flow_task.condition(self)

    def activate_next(self):
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

    task_type = 'IF'
    activation_class = IfActivation

    def __init__(self, cond, **kwargs):
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

    def Then(self, node):
        result = copy(self)
        result._on_true = node
        return result

    def Else(self, node):
        result = copy(self)
        result._on_false = node
        return result

    @property
    def condition(self):
        return self._condition
