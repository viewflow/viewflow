from django.db import connection
from django.utils.timezone import now
from viewflow import this

from ..activation import Activation
from ..exceptions import FlowRuntimeError
from ..signals import task_finished
from ..status import STATUS
from ..token import Token
from ..base import Node, Edge
from .join import Join
from . import mixins


class SplitActivation(Activation):
    """Parallel split gateway activation."""

    def __init__(self, *args, **kwargs):  # noqa D102
        self.next_tasks = []
        super().__init__(*args, **kwargs)

    @Activation.status.super()
    def activate(self):
        """Calculate nodes list to activate."""
        for node, cond, data_source in self.flow_task._branches:
            if cond and not cond(self):
                continue
            else:
                self.next_tasks.append((node, None))

        if not self.next_tasks:
            raise FlowRuntimeError(
                "No next task available for {}".format(self.flow_task.name)
            )

    @Activation.status.super()
    def create_next(self):
        """Activate next tasks for parallel execution.

        Each task would have a new execution token attached,
        the Split task token as a common prefix.
        """
        token_source = Token.split_token_source(self.task.token, self.task.pk)

        next_tasks = [
            (task, data) for task, data in self.next_tasks if not isinstance(task, Join)
        ] + [(task, data) for task, data in self.next_tasks if isinstance(task, Join)]

        for n, (next_task, data) in enumerate(next_tasks, 1):
            yield next_task._create(
                prev_activation=self, token=next(token_source), data=data
            )


class Split(
    Node,
):
    """
    Represents a parallel split gateway in a workflow, allowing branching into multiple parallel paths.

    Methods:
        - `Next(node, case=None, data_source=None)`: Defines the subsequent node in the workflow.
          - `node`: The next node to execute.
          - `case` (optional): A callable that takes an activation and returns `True` if the node should be activated.
          - `data_source` (optional): A callable that takes an activation and returns a list of data items, creating an instance of the node for each item, with `task.data` set to the item.
        - `Always(node)`: A shortcut to define a subsequent node that is always executed.

    Example:
        ```python
        flow.Split()
            .Next(
                this.approve,
                case=act.process.approved,
                data_source=lambda activation: [{"sample": "test task 1"}, {"sample": "test task 2"}],
            )
            .Always(this.required)
        ```

    In this example:
        - The `approve` node is executed multiple times based on the `data_source` list.
        - The `required` node is always executed unconditionally in parallel.

    Notes:
        - If `case` is not provided, the node is always activated.
        - If `data_source` is not provided, the node is created only once.
    """

    activation_class = SplitActivation

    task_type = "PARALLEL_GATEWAY"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <path class="gateway" d="M25,0L50,25L25,50L0,25L25,0"/>
            <text class="gateway-marker" font-size="32px" x="25" y="35">+</text>
        """,
    }

    bpmn_element = "parallelGateway"

    def __init__(self, **kwargs):  # noqa D102
        super(Split, self).__init__(**kwargs)
        self._activate_next = []

    def _outgoing(self):
        for next_node, cond, _ in self._activate_next:
            edge_class = "cond_true" if cond else "default"
            yield Edge(src=self, dst=next_node, edge_class=edge_class)

    def _resolve(self, instance):
        super()._resolve(instance)

        self._activate_next = [
            (
                this.resolve(instance, node),
                this.resolve(instance, cond),
                this.resolve(instance, data_source),
            )
            for node, cond, data_source in self._activate_next
        ]

    @property
    def _branches(self):
        return self._activate_next

    def Next(self, node, case=None):
        """Node to activate if condition is true.

        :param cond: Callable[activation] -> bool

        """
        self._activate_next.append((node, case, None))
        return self

    def Always(self, node):
        return self.Next(node)


class SplitFirstActivation(SplitActivation):
    """
    Parallel split gateway activation. As soon as the first task is completed,
    the remaining tasks are cancelled.
    """

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def activate(self):
        self.task.started = now()
        self.task.save()
        super().activate.original()

    @Activation.status.transition(source=STATUS.STARTED)
    def create_next(self):
        yield from super().create_next.original()

    @Activation.status.transition(source=[STATUS.STARTED], target=STATUS.CANCELED)
    def cancel(self):
        self.task.finished = now()
        self.task.save()

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.DONE)
    def done(self):
        assert connection.in_atomic_block
        self.task.finished = now()
        self.task.save()
        task_finished.send(sender=self.flow_class, process=self.process, task=self.task)


class SplitFirst(
    Split,
):
    """
    Parallel split, as soon as the first task is completed, the remaining tasks
    are cancelled.
    """

    activation_class = SplitFirstActivation

    def _ready(self):
        task_finished.connect(self.on_task_done, sender=self.flow_class)

    def _cancel_active_tasks(self, active_tasks):
        activations = [task.flow_task.activation_class(task) for task in active_tasks]

        not_cancellable = [
            activation
            for activation in activations
            if not activation.cancel.can_proceed()
        ]
        if not_cancellable:
            raise FlowRuntimeError(
                "Can't cancel {}".format(
                    ",".join(activation.task for activation in not_cancellable)
                )
            )

        for activation in activations:
            activation.cancel()

    def on_task_done(self, **signal_kwargs):
        task = signal_kwargs["task"]
        outgoing_flow_tasks = [task.dst for task in self._outgoing()]
        if task.flow_task in [flow_task for flow_task in outgoing_flow_tasks]:
            split_task = self.flow_class.task_class._default_manager.get(
                process=task.process, flow_task=self, status=STATUS.STARTED
            )

            activation = self.activation_class(split_task)

            active_tasks = (
                self.flow_class.task_class._default_manager.filter(
                    process=task.process, flow_task__in=outgoing_flow_tasks
                )
                .exclude(status__in=[STATUS.DONE, STATUS.CANCELED])
                .exclude(pk=task.pk)
            )
            self._cancel_active_tasks(active_tasks)

            activation.done()
