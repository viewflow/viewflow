from django.utils.timezone import now
from viewflow import this
from ..activation import Activation, leading_tasks_canceled
from ..base import Node
from ..status import STATUS
from ..signals import task_started, task_finished
from . import mixins


class HandleActivation(mixins.NextNodeActivationMixin, Activation):
    @Activation.status.super()
    def activate(self):
        """Do nothing on sync call"""

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def run(self, func, **kwargs):
        self.task.started = now()
        task_started.send(sender=self.flow_class, process=self.process, task=self.task)
        return func(self, **kwargs) if func else self.process

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.DONE)
    def complete(self):
        """Complete task and create next."""
        super().complete.original()

    @Activation.status.transition(source=STATUS.STARTED)
    def execute(self):
        self.complete()
        self.activate_next()

    @Activation.status.transition(
        source=STATUS.DONE, target=STATUS.CANCELED, conditions=[leading_tasks_canceled]
    )
    def undo(self):
        if self.flow_task._undo_func is not None:
            self.flow_task._undo_func(self)
        super().undo.original()

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.CANCELED)
    def cancel(self):
        self.task.finished = now()
        self.task.save()


class Handle(mixins.NextNodeMixin, Node):
    """
    Task to be executed outside of the flow.
    """

    task_type = "FUNCTION"
    activation_class = HandleActivation

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

    def __init__(self, func=None, undo_func=None, **kwargs):
        super().__init__(**kwargs)
        self._func = func
        self._undo_func = undo_func

    def _create_wrapper_function(self, origin_func, task):
        def func(**kwargs):
            with self.flow_class.lock(task.process.pk):
                task.refresh_from_db()
                activation = self.activation_class(task)
                result = activation.run(origin_func, **kwargs)
                activation.execute()
                return result

        return func

    def run(self, task, **kwargs):
        func = this.resolve(self.flow_class.instance, self._func)
        wrapper = self._create_wrapper_function(func, task)
        return wrapper(**kwargs)
