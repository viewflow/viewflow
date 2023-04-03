from django.utils.timezone import now
from viewflow.this_object import this
from ..activation import Activation, leading_tasks_canceled
from ..base import Node
from ..exceptions import FlowRuntimeError
from ..status import STATUS
from . import mixins


class JoinActivation(mixins.NextNodeActivationMixin, Activation):
    """Activation for parallel Join node."""

    def __init__(self, *args, **kwargs):  # noqa D102
        self.next_task = None
        super(JoinActivation, self).__init__(*args, **kwargs)

    @classmethod
    def create(cls, flow_task, prev_activation, token):
        """
        Join and, if all incoming paths are completed, continue execution.

        Join task is created on the first activation. Subsequent
        activations will look for an existing Join Task instance.
        """
        flow_class = flow_task.flow_class
        task_class = flow_class.task_class

        # lookup for an active join task instance
        tasks = task_class._default_manager.filter(
            flow_task=flow_task,
            process=prev_activation.process,
            status__in=[STATUS.NEW, STATUS.STARTED],
        )

        if len(tasks) > 1:
            raise FlowRuntimeError("More than one join instance for process found")

        task = tasks.first()

        if not task:
            # Create new Join Node
            if token.is_split_token():
                token = token.get_base_split_token()

            task = flow_class.task_class.objects.create(
                process=prev_activation.process, flow_task=flow_task, token=token
            )

        task.previous.add(prev_activation.task)
        activation = cls(task)

        return activation

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    @Activation.status.transition(source=STATUS.STARTED)
    def activate(self):
        """Do nothing on a sync call"""
        if self.task.started is None:
            self.task.started = now()
            self.task.save()

    @Activation.status.transition(
        source=STATUS.STARTED, target=STATUS.DONE, conditions=[this.is_done]
    )
    def complete(self):
        """Complete the join task and create next."""
        #  with self.exception_guard(): TODO exception guard on join ??
        super().complete.original()

    def cancel_active_tasks(self, active_tasks):
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

    def is_done(self):
        """
        Check that process can be continued futher.

        Join check the all task state in db with the common token prefix.

        Join node would continue execution if all incoming tasks are DONE or CANCELED.
        """
        join_prefixes = set(
            prev.token.get_common_split_prefix(self.task.token, prev.pk)
            for prev in self.task.previous.exclude(status=STATUS.CANCELED).all()
        )

        if len(join_prefixes) > 1:
            raise FlowRuntimeError(
                f"Multiple tokens {join_prefixes} came to join { self.flow_task.name}"
            )

        join_token_prefix = next(iter(join_prefixes))

        active_tasks = self.flow_class.task_class._default_manager.filter(
            process=self.process, token__startswith=join_token_prefix
        ).exclude(status__in=[STATUS.DONE, STATUS.CANCELED])

        if self.flow_task._continue_on_condition:
            continue_result = self.flow_task._continue_on_condition(self, active_tasks)
            if continue_result:
                self.cancel_active_tasks(active_tasks)
                return True

        return not active_tasks.exists()

    @Activation.status.transition(
        source=[STATUS.NEW, STATUS.STARTED], target=STATUS.CANCELED
    )
    def cancel(self):
        self.task.finished = now()
        self.task.save()


class Join(
    mixins.NextNodeMixin,
    Node,
):
    """Wait for one or all incoming links and activates next path."""

    activation_class = JoinActivation

    task_type = "JOIN"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <path class="gateway" d="M25,0L50,25L25,50L0,25L25,0"/>
            <text class="gateway-marker" font-size="32px" x="25" y="35">+</text>
        """,
    }

    bpmn_element = "parallelGateway"

    def __init__(self, continue_on_condition=None, **kwargs):  # noqa D102
        super(Join, self).__init__(**kwargs)
        self._continue_on_condition = continue_on_condition

    def _resolve(self, cls):
        super()._resolve(cls)
        self._continue_on_condition = this.resolve(cls, self._continue_on_condition)
