import copy

from viewflow.fsm import State
from ..activation import Activation, STATUS
from ..base import Node
from . import mixins


class ObsoleteActivation(Activation):
    @Activation.status.transition(
        source=State.ANY, target=STATUS.CANCELED,
        conditions=[lambda a: a.task.status != STATUS.CANCELED])
    def cancel(self):
        """ Cancel existing task. """
        super(ObsoleteActivation, self).cancel.original()


class Obsolete(
    Node
):
    """Missing node instance."""

    activation_class = ObsoleteActivation

    task_type = 'OBSOLETE'

    shape = {
        'width': 0,
        'height': 0,
        'svg': ''
    }

    bpmn_element = None

    def _outgoing(self):
        return
        yield

    def create_node(self, name):
        """
        Create real node instance for missing entry
        """
        obsolete = copy.copy(self)
        obsolete.name = name
        return obsolete
