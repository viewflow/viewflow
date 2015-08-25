from viewflow.activation import AbstractGateActivation
from viewflow.flow import base
from viewflow.token import Token


class DynamicSplitActivation(AbstractGateActivation):
    def calculate_next(self):
        self._split_count = self.flow_task._task_count_callback(self.process)

    def activate_next(self):
        if self._split_count:
            token_source = Token.split_token_source(self.task.token, self.task.pk)
            for _ in range(self._split_count):
                self.flow_task._next.activate(prev_activation=self, token=next(token_source))


class DynamicSplit(base.NextNodeMixin,
                   base.UndoViewMixin,
                   base.CancelViewMixin,
                   base.PerformViewMixin,
                   base.DetailsViewMixin,
                   base.Gateway):
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
    activation_cls = DynamicSplitActivation

    def __init__(self, callback):
        super(DynamicSplit, self).__init__()
        self._task_count_callback = callback
