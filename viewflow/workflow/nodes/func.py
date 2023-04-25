from django.utils.timezone import now

from viewflow import this
from ..activation import Activation
from ..base import Node
from ..status import STATUS
from ..signals import task_started
from . import mixins


class FunctionActivation(mixins.NextNodeActivationMixin, Activation):
    """
    Handle  Activation.

    Executes a callback immediately.
    """

    @Activation.status.super()
    def activate(self):
        """Perform the callback within current exception propagation strategy."""
        with self.exception_guard():
            self.task.started = now()
            task_started.send(
                sender=self.flow_class, process=self.process, task=self.task
            )
            self.flow_task._func(self)

    @Activation.status.transition(source=STATUS.ERROR, target=STATUS.DONE)
    def retry(self):
        """Retry the next node calculation and activation."""
        self.activate.original()


class Function(mixins.NextNodeMixin, mixins.NodePermissionMixin, Node):
    """
    Callback executed synchronously on a task activation.
    """

    activation_class = FunctionActivation

    task_type = "FUNCTION"

    shape = {
        "width": 150,
        "height": 100,
        "text-align": "middle",
        "svg": """
            <rect class="task" width="150" height="100" rx="5" ry="5"/>
            <path class="task-marker"
                  d="m 15,20 c 10,-6 -8,-8 3,-15 l -9,0 c -11,7 7,9 -3,15 z
                     m -7,-12 l 5,0 m -4.5,3 l 4.5,0 m -3,3 l 5,0 m -4,3 l 5,0"/>
        """,
    }

    bpmn_element = "scriptTask"

    def __init__(self, func, **kwargs):  # noqa D102
        super().__init__(**kwargs)
        self._func = func

    def _resolve(self, instance):
        super()._resolve(instance)
        self._func = this.resolve(instance, self._func)
