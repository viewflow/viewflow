from ..activation import EndActivation
from .. import Event, mixins


class End(mixins.TaskDescriptionMixin,
          mixins.DetailViewMixin,
          mixins.UndoViewMixin,
          mixins.CancelViewMixin,
          mixins.PerformViewMixin,
          Event):

    task_type = 'END'
    activation_class = EndActivation

    def __init__(self, **kwargs):
        super(End, self).__init__(**kwargs)

    def _outgoing(self):
        return iter([])
