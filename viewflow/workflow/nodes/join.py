from django.db import transaction
from django.utils.timezone import now
from viewflow.this_object import this
from ..activation import Activation
from ..base import Node
from ..exceptions import FlowRuntimeError
from ..status import STATUS
from . import mixins


class JoinActivation(mixins.NextNodeActivationMixin, Activation):
    """Activation for parallel Join node."""

    type: str = "join"

    def __init__(self, *args, **kwargs):  # noqa D102
        self.next_task = None
        super().__init__(*args, **kwargs)

    @classmethod
    def create(cls, flow_task, prev_activation, token, data=None, seed=None):
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

            task = flow_class.task_class(
                process=prev_activation.process,
                flow_task=flow_task,
                token=token,
            )
            task.data = data if data is not None else {}
            task.seed = seed
            task.save()
        else:
            # todo resolve task_data and seed
            pass

        task.previous.add(prev_activation.task)
        activation = cls(task)

        return activation

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    @Activation.status.transition(source=STATUS.STARTED)
    def activate(self):
        if self.task.started is None:
            self.task.started = now()
            self.task.save()

    @Activation.status.transition(
        source=STATUS.STARTED, target=STATUS.DONE, conditions=[this.is_done]
    )
    def complete(self):
        """Complete the join task and create next.

        The join's own work -- verifying a single incoming token, running the
        ``continue_on_condition`` cancellation of still-active branches, and the
        base completion -- runs inside the exception guard and a savepoint.

        On error the guard follows the activation context: a background trigger
        (``propagate_exception=False``, e.g. a Job node completing) records
        ``STATUS.ERROR`` on the join and the savepoint rolls back any partial
        cancel, so the process is left recoverable instead of crashing the
        worker; a user/synchronous trigger propagates the exception up to the
        node that triggered the join.
        """
        with self.exception_guard(), transaction.atomic(savepoint=True):
            join_prefixes = self._join_token_prefixes()
            if len(join_prefixes) > 1:
                raise FlowRuntimeError(
                    f"Multiple tokens {join_prefixes} came to join {self.flow_task.name}"
                )

            if join_prefixes and self.flow_task._continue_on_condition:
                active_tasks = self._active_join_tasks(next(iter(join_prefixes)))
                if active_tasks.exists() and self.flow_task._continue_on_condition(
                    self, active_tasks
                ):
                    self.cancel_active_tasks(active_tasks)

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
                    ",".join(str(activation.task) for activation in not_cancellable)
                )
            )

        for activation in activations:
            activation.cancel()

    def _join_token_prefixes(self):
        """Common split-token prefixes of the non-cancelled incoming tasks."""
        return set(
            prev.token.get_common_split_prefix(self.task.token, prev.pk)
            for prev in self.task.previous.exclude(
                status__in=[STATUS.CANCELED, STATUS.REVIVED]
            ).all()
        )

    def _active_join_tasks(self, join_token_prefix):
        """Still-running tasks sharing the join's token prefix."""
        return self.flow_class.task_class._default_manager.filter(
            process=self.process, token__startswith=join_token_prefix
        ).exclude(status__in=[STATUS.DONE, STATUS.CANCELED, STATUS.REVIVED])

    def is_done(self):
        """
        Check that process can be continued further.

        Join checks all task states in db with the common token prefix. It
        continues execution if all incoming tasks are DONE or CANCELED, or if
        the ``continue_on_condition`` predicate allows it.

        This is a pure, side-effect-free predicate: it neither cancels tasks nor
        raises. An ambiguous multi-token state is reported as "done" so that
        ``complete()`` runs and surfaces the error under the exception guard,
        rather than crashing the condition check.
        """
        join_prefixes = self._join_token_prefixes()
        if len(join_prefixes) != 1:
            # >1 is a flow-integrity error, handled in complete(); 0 means
            # nothing has arrived to join yet.
            return len(join_prefixes) > 1

        active_tasks = self._active_join_tasks(next(iter(join_prefixes)))

        if self.flow_task._continue_on_condition:
            if self.flow_task._continue_on_condition(self, active_tasks):
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

    def __init__(
        self, continue_on_condition=None, cancel_active=True, **kwargs
    ):  # noqa D102
        super().__init__(**kwargs)
        self._cancel_active: bool = cancel_active
        self._continue_on_condition = continue_on_condition

    def _resolve(self, cls):
        super()._resolve(cls)
        self._continue_on_condition = this.resolve(cls, self._continue_on_condition)
