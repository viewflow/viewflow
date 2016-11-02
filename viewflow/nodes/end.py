from ..activation import EndActivation
from .. import Event, mixins


class End(mixins.TaskDescriptionMixin,
          mixins.DetailViewMixin,
          mixins.UndoViewMixin,
          mixins.CancelViewMixin,
          mixins.PerformViewMixin,
          Event):
    """End of the flow.

    If no other parallel activities exists, finishes the whole
    process.
    """

    task_type = 'END'
    activation_class = EndActivation

    def __init__(self, **kwargs):  # noqa D102
        super(End, self).__init__(**kwargs)

    def _outgoing(self):
        return iter([])
