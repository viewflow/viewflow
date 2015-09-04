"""
Finishes the process and cancels all other active tasks
"""

from ..activation import EndActivation
from . import base


class End(base.TaskDescriptionMixin,
          base.DetailsViewMixin,
          base.UndoViewMixin,
          base.CancelViewMixin,
          base.PerformViewMixin,
          base.Event):
    """
    Ends process event.
    """
    task_type = 'END'
    activation_cls = EndActivation

    def __init__(self, **kwargs):
        super(End, self).__init__(**kwargs)

    def _outgoing(self):
        return iter([])
