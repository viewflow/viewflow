from typing import Callable, Dict, Any, Optional
from django.utils.timezone import now

from viewflow import this
from viewflow.workflow.models import Process
from ..activation import Activation
from ..base import Node
from ..signals import task_started, flow_finished
from ..status import STATUS
from .start import StartActivation, StartHandle
from . import mixins


def subprocess_finished(activation: Activation) -> bool:
    return all(
        process.status == STATUS.DONE
        for process in Process._default_manager.filter(
            parent_task=activation.task,
        ).exclude(
            status=STATUS.CANCELED,
        )
    )


class StartSubprocess(mixins.NextNodeMixin, Node):
    """Start subprocess handle"""

    task_type = "START"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event" cx="25" cy="25" r="25"/>
        """,
    }

    bpmn_element = "startEvent"

    activation_class = StartActivation

    def __init__(self, func=None, **kwargs):
        super().__init__(**kwargs)
        self._func = func

    def run(self, _parent_task, **kwargs):
        func = this.resolve(self.flow_class.instance, self._func)

        def wrapper(**kwargs):
            activation = self.activation_class.create(self, None, _parent_task.token)
            activation.process.parent_task = _parent_task
            if func:
                func(activation, **kwargs)
            activation.execute()
            return activation

        return wrapper(**kwargs)


class SubprocessActivation(mixins.NextNodeActivationMixin, Activation):
    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def activate(self):
        with self.exception_guard():
            self.task.started = now()
            self.task.save()
            task_started.send(
                sender=self.flow_class, process=self.process, task=self.task
            )

            subprocess_kwargs = {}
            if self.flow_task.get_subprocess_kwargs:
                subprocess_kwargs = self.flow_task.get_subprocess_kwargs(self)
            self.flow_task.start_subprocess_task.run(
                _parent_task=self.task, **subprocess_kwargs
            )

    @Activation.status.transition(
        source=STATUS.STARTED, target=STATUS.DONE, conditions=[subprocess_finished]
    )
    def complete(self):
        """Complete task and create next."""
        super().complete.original()

    @Activation.status.transition(source=STATUS.STARTED)
    def execute(self):
        self.complete()
        self.activate_next()

    @Activation.status.transition(source=STATUS.ERROR, target=STATUS.DONE)
    def retry(self):
        """Retry the next node calculation and activation."""
        self.activate.original()


class Subprocess(mixins.NextNodeMixin, Node):
    """
    The ``Subprocess`` node in a flow.
    """

    task_type = "SUBPROCESS"
    activation_class = SubprocessActivation

    shape = {
        "width": 150,
        "height": 100,
        "text-align": "middle",
        "svg": """
            <rect class="task" width="150" height="100" rx="5" ry="5" style="stroke-width:5"/>
        """,
    }

    def __init__(
        self,
        start_subprocess_task: StartHandle,
        get_subprocess_kwargs: Optional[Callable[[Activation], Dict[str, Any]]] = None,
        **kwargs
    ):
        self.start_subprocess_task = start_subprocess_task
        self.get_subprocess_kwargs = get_subprocess_kwargs
        super().__init__(**kwargs)

    def _ready(self):
        flow_finished.connect(
            self.on_flow_finished, sender=self.start_subprocess_task.flow_class
        )

    def on_flow_finished(self, **signal_kwargs):
        process = signal_kwargs["process"]
        if process.parent_task and process.parent_task.flow_task == self:
            with process.parent_task.activation() as activation:
                if activation.complete.can_proceed():
                    activation.execute()


class NSubprocessActivation(SubprocessActivation):
    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def activate(self):
        with self.exception_guard():
            self.task.started = now()
            self.task.save()

            for item in self.flow_task.subitem_source(self.process):
                self.flow_task.start_subprocess_task.run(
                    _parent_task=self.task, item=item
                )

            task_started.send(
                sender=self.flow_class, process=self.process, task=self.task
            )


class NSubprocess(Subprocess):
    """
    The ``NSubprocess`` node in a flow.

       This node is used to start multiple instances of a subprocess flow within a
       parent flow. Each instance processes a different item, and all subprocesses
       must be completed before the parent flow can proceed.


       .. code-block:: python

           class ExampleSubFlow(flow.Flow):
               start = flow.StartHandle(this.start_func).Next(this.task) task =
               flow.Handle(this.task_func).Next(this.end)
               end = flow.End()

               def start_func(self, activation, item=0):
                   # instantialed with one of 1, 2, 3, 4 as item
                   activation.process.data = item

               def task_func(self, activation):
                   activation.process.data += 100

           class MainFlowWithNSubprocess(flow.Flow):
               start = flow.StartFunction().Next(this.nsubprocess) nsubprocess =
               flow.NSubprocess(ExampleSubFlow.start, lambda p: [1, 2, 3, 4]).Next(this.end)
               end = flow.End()
    """

    task_type = "SUBPROCESS"
    activation_class = NSubprocessActivation

    shape = {
        "width": 150,
        "height": 100,
        "text-align": "middle",
        "svg": """
            <rect class="task" width="150" height="100" rx="5" ry="5" style="stroke-width:5"/>
        """,
    }

    def __init__(self, start_subprocess_task, subitem_source, **kwargs):
        self.start_subprocess_task = start_subprocess_task
        self.subitem_source = subitem_source
        super().__init__(start_subprocess_task, **kwargs)
