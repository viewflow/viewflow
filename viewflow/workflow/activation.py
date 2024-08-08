import json
import traceback
from contextlib import ContextDecorator
from typing import Any, List, Optional, Set

from django.db import connection, transaction
from django.utils.timezone import now

from viewflow import fsm
from .context import context
from .signals import task_finished, task_failed
from .status import STATUS, PROCESS


def parent_tasks_completed(activation: "Activation") -> bool:
    """
    Check if all parent tasks are completed.

    Canceled task could be recreated iff all parent task was not cancelled.

    Args:
        activation (Activation): The current activation instance.

    Returns:
        bool: True if all parent tasks are completed, False otherwise.
    """
    previous = activation.task.previous.values("status")
    completed = (STATUS.DONE, STATUS.REVIVED)
    return all(lambda task: task.status in completed, previous)


def leading_tasks_canceled(activation: "Activation") -> bool:
    """
    Check if all leading tasks are canceled.

    Task could be undone iff no outgoing uncancelled tasks are exists.

    Args:
        activation (Activation): The current activation instance.

    Returns:
        bool: True if all leading tasks are canceled, False otherwise.
    """
    non_canceled_count = (
        activation.task.leading.exclude(status=STATUS.CANCELED)
        .exclude(status=STATUS.REVIVED)
        .count()
    )
    return non_canceled_count == 0


def process_not_cancelled(activation: "Activation") -> bool:
    """
    Check if the process is not canceled.

    Args:
        activation (Activation): The current activation instance.

    Returns:
        bool: True if the process is not canceled, False otherwise.
    """
    return activation.process.status != PROCESS.CANCELED


def has_manage_permission(activation: "Activation", user: Any) -> bool:
    """
    Check if the user has manage permission.

    Args:
        activation (Activation): The current activation instance.
        user (Any): The user instance.

    Returns:
        bool: True if the user has manage permission, False otherwise.
    """
    return activation.flow_class.instance.has_manage_permission(user)


class Activation:
    """
    Base class for flow task activations.

    Activation is responsible for flow task state management and persistence.
    Each activation status change is restricted by a simple finite state automaton.
    """

    status: fsm.State = fsm.State(STATUS, default=STATUS.NEW)
    type: str = "node"

    def __init__(self, task: Any) -> None:
        """
        Instantiate an activation.

        Args:
            task (Any): The task instance associated with the activation.
        """
        self.task = task
        self.process = task.process.coerced

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Activation):
            return False
        return self.task == other.task

    def __hash__(self) -> int:
        return hash(self.task)

    @status.setter()
    def _set_status(self, value: Any) -> None:
        """Set the status to the underline task."""
        self.task.status = value

    @status.getter()
    def _get_status(self) -> Any:
        """Get the status of the activated task."""
        return self.task.status

    @property
    def flow_task(self) -> Any:
        """Get the flow task associated with the activation."""
        return self.task.flow_task

    @property
    def flow_class(self) -> Any:
        """Get the flow class associated with the activation."""
        return self.flow_task.flow_class

    def exception_guard(self) -> ContextDecorator:
        """
        Perform activation action inside a transaction.

        Handle and propagate exception depending on activation context state.
        """

        class ExceptionGuard(ContextDecorator):
            def __enter__(self):
                return self

            def __exit__(self_eg, exc_type, exc_val, exc_tb):
                if exc_type is not None:
                    if not context.propagate_exception:
                        # Keep error state
                        tb = exc_val.__traceback__
                        while tb.tb_next:
                            tb = tb.tb_next

                        try:
                            serialized_locals = json.dumps(
                                tb.tb_frame.f_locals, default=lambda obj: str(obj)
                            )
                        except Exception as ex:
                            serialized_locals = json.dumps(
                                {"_serialization_exception": str(ex)}
                            )

                        self.task.data["_exception"] = {
                            "title": str(exc_val),
                            "traceback": traceback.format_exc(),
                            "locals": json.loads(serialized_locals),
                        }

                        # Set status
                        self.task.finished = now()
                        self._set_status(STATUS.ERROR)
                        self.task.save()
                        task_failed.send(
                            sender=self.flow_class, process=self.process, task=self.task
                        )
                        # self.transaction.__exit__(exc_type, exc_val, exc_tb)
                        return True  # Suppress the exception
                    else:
                        # self.transaction.__exit__(exc_type, exc_val, exc_tb)
                        return False  # Propagate the exception

        return ExceptionGuard()

    @classmethod
    def create(
        cls,
        flow_task: Any,
        prev_activation: "Activation",
        token: Any,
        data: Optional[Any] = None,
        seed: Optional[Any] = None,
    ) -> "Activation":
        """
        Instantiate and persist a new flow task.

        Args:
            flow_task (Any): The flow task instance.
            prev_activation (Activation): The previous activation instance.
            token (Any): The token for the new task.
            data (Optional[Any]): Additional data for the new task.

        Returns:
            Activation: The newly created activation instance.
        """
        flow_class = flow_task.flow_class
        task = flow_class.task_class(
            process=prev_activation.process,
            flow_task=flow_task,
            token=token,
        )
        task.data = data if data is not None else {}
        task.seed = seed
        task.save()
        task.previous.add(prev_activation.task)
        return cls(task)

    @status.transition(source=STATUS.NEW)
    def activate(self) -> None:
        """Activate the task."""
        raise NotImplementedError(
            f"{self.__class__.__name__} class should override act() method"
        )

    @status.transition(source=STATUS.DONE)
    def create_next(self) -> None:
        """Create the next task in the flow."""
        raise NotImplementedError(
            f"{self.__class__.__name__} class should override create_next() method"
        )

    @status.transition(source=STATUS.NEW, target=STATUS.DONE)
    def complete(self) -> None:
        """Complete the current task."""
        assert connection.in_atomic_block
        self.task.finished = now()
        self.task.save()
        task_finished.send(sender=self.flow_class, process=self.process, task=self.task)

    def _activate_next(self, activations: Set["Activation"]) -> None:
        """Activate the next set of tasks."""
        while activations:
            join_activations = {act for act in activations if act.type == "join"}
            task_activations = activations - join_activations

            if task_activations:
                for current_activation in task_activations:
                    if current_activation.activate.can_proceed():
                        current_activation.activate()

                    if current_activation.complete.can_proceed():
                        current_activation.complete()

                activations = {
                    next_activation
                    for current_activation in activations
                    if current_activation.create_next.can_proceed()
                    for next_activation in current_activation.create_next()
                }
                activations.update(join_activations)
            elif join_activations:
                # process first join activation
                current_activation = join_activations.pop()
                if current_activation.activate.can_proceed():
                    current_activation.activate()

                if current_activation.complete.can_proceed():
                    current_activation.complete()

                activations = set()
                if current_activation.create_next.can_proceed():
                    activations = {
                        next_activation
                        for next_activation in current_activation.create_next()
                    }
                activations.update(join_activations)

    @status.transition(source=STATUS.DONE)
    def activate_next(self) -> None:
        """Activate the next task in the flow."""
        assert connection.in_atomic_block
        activations = set(self.create_next())
        self._activate_next(activations)

    @status.transition(
        source=STATUS.DONE,
        target=STATUS.CANCELED,
        conditions=[leading_tasks_canceled],
        permission=has_manage_permission,
    )
    def undo(self) -> None:
        """Undo the current task."""
        self.task.finished = now()
        self.task.save()

    @status.transition(
        source=[STATUS.CANCELED, STATUS.ERROR],
        target=STATUS.REVIVED,
        permission=has_manage_permission,
    )
    def revive(self) -> Any:
        """
        Recreate and activate cancelled task
        """
        flow_class = self.flow_class
        task = flow_class.task_class(
            process=self.process,
            flow_task=self.flow_task,
            token=self.task.token,
        )
        task.seed = self.task.seed
        task.data = self.task.data
        task.artifact = self.task.artifact
        task.save()

        for prev_task in self.task.previous.all():
            task.previous.add(prev_task)
        task.previous.add(self.task)
        self.task.save(update_fields=["status"])

        activations = set([type(self)(task)])
        self._activate_next(activations)
        return task

    def get_outgoing_transitions(self) -> List[fsm.Transition]:
        """Get the outgoing transitions for the current status."""
        return self.__class__.status.get_outgoing_transitions(self.status)

    def get_available_transitions(self, user) -> List[fsm.Transition]:
        """Get the available transitions for the current status and user."""
        return self.__class__.status.get_available_transitions(self, self.status, user)
