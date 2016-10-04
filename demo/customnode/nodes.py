from copy import copy

from viewflow import Gateway, mixins
from viewflow.exceptions import FlowRuntimeError
from viewflow.activation import AbstractGateActivation
from viewflow.token import Token
from viewflow.flow import views


class DynamicSplitActivation(AbstractGateActivation):
    def calculate_next(self):
        self._split_count = self.flow_task._task_count_callback(self.process)

    def activate_next(self):
        if self._split_count:
            token_source = Token.split_token_source(self.task.token, self.task.pk)
            for _ in range(self._split_count):
                self.flow_task._next.activate(prev_activation=self, token=next(token_source))
        elif self.flow_task._ifnone_next_node is not None:
            self.flow_task._ifnone_next_node.activate(prev_activation=self, token=self.task.token)
        else:
            raise FlowRuntimeError("{} activated with zero and no IfNone nodes specified".format(self.flow_task.name))


class DynamicSplit(mixins.NextNodeMixin,
                   mixins.UndoViewMixin,
                   mixins.CancelViewMixin,
                   mixins.PerformViewMixin,
                   mixins.DetailViewMixin,
                   Gateway):
    """
    Activates several outgoing task instances depends on callback value

    Example::

        spit_on_decision = flow.DynamicSplit(lambda p: 4) \\
            .Next(this.make_decision)

        make_decision = flow.View(MyView) \\
            .Next(this.join_on_decision)

        join_on_decision = flow.Join() \\
            .Next(this.end)
    """
    task_type = 'SPLIT'

    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    perform_view_class = views.PerformTaskView
    undo_view_class = views.UndoTaskView

    activation_class = DynamicSplitActivation

    def __init__(self, callback):
        super(DynamicSplit, self).__init__()
        self._task_count_callback = callback
        self._ifnone_next_node = None

    def _resolve(self, resolver):
        super(DynamicSplit, self)._resolve(resolver)
        self._ifnone_next_node = resolver.get_implementation(self._ifnone_next_node)

    def IfNone(self, node):
        result = copy(self)
        result._ifnone_next_node = node
        return result
