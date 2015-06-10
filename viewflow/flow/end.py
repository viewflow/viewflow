"""
Finishes the process and cancels all other active tasks
"""

from ..activation import EndActivation
from . import base


class End(base.DetailsViewMixin,
          base.UndoViewMixin,
          base.CancelViewMixin,
          base.PerformViewMixin,
          base.Event):
    """
    Ends process event.
    """
    task_type = 'END'
    activation_cls = EndActivation

    def __init__(self):
        super(End, self).__init__()

    def _outgoing(self):
        return iter([])
