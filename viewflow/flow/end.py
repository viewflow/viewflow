"""
Finishes the process and cancells all other active tasks
"""

from viewflow.flow.base import Event
from viewflow.activation import EndActivation


class End(Event):
    """
    End process event
    """
    task_type = 'END'
    activation_cls = EndActivation

    def __init__(self):
        super(End, self).__init__()

    def _outgoing(self):
        return iter([])
