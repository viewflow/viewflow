import copy

from viewflow.fsm import State
from ..activation import Activation, STATUS, has_manage_permission
from ..base import Node
from . import mixins


class ObsoleteActivation(Activation):
    @Activation.status.transition(
        source=State.ANY,
        target=STATUS.CANCELED,
        conditions=[lambda a: a.task.status != STATUS.CANCELED],
        permission=has_manage_permission,
    )
    def cancel(self):
        if self.flow_task._cancel_func is not None:
            self.flow_task._cancel_func(self)
        self.task.save()


class Obsolete(Node):
    """Missing node instance."""

    activation_class = ObsoleteActivation

    task_type = "OBSOLETE"

    shape = {"width": 0, "height": 0, "svg": ""}

    bpmn_element = None

    def __init__(self, cancel_func=None, undo_func=None, **kwargs):
        super().__init__(**kwargs)
        self._undo_func = undo_func
        self._cancel_func = cancel_func

    def _outgoing(self):
        return
        yield

    def create_node(self, name, flow_class):
        """
        Create real node instance for missing entry
        """
        obsolete = copy.copy(self)
        obsolete.name = name
        obsolete.flow_class = flow_class
        return obsolete
