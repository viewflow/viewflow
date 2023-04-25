from django.db import transaction
from django.utils.timezone import now

from ..base import Node
from ..activation import Activation, process_not_cancelled
from ..status import STATUS, PROCESS
from ..signals import task_started, task_finished, flow_finished


class EndActivation(Activation):
    """Activation that finishes the flow process."""

    @Activation.status.transition(
        source=STATUS.DONE, target=STATUS.CANCELED, conditions=[process_not_cancelled]
    )
    def undo(self):
        self.process.finished = None
        self.process.status = PROCESS.NEW
        self.process.save()
        super().undo.original()

    @Activation.status.super()
    def activate(self):
        """
        Finalize the flow. If there is no active task, process marked as finished.
        """
        with transaction.atomic(savepoint=True):
            self.task.started = now()
            task_started.send(
                sender=self.flow_class, process=self.process, task=self.task
            )

            active_tasks_count = (
                self.flow_class.task_class._default_manager.filter(
                    process=self.process, finished__isnull=True
                ).exclude(pk=self.task.pk)
            ).count()

            if active_tasks_count == 0:
                self.process.status = STATUS.DONE
                self.process.finished = now()
                self.process.save()

            task_finished.send(
                sender=self.flow_class, process=self.process, task=self.task
            )
            if active_tasks_count == 0:
                flow_finished.send(
                    sender=self.flow_class, process=self.process, task=self.task
                )

    @Activation.status.super()
    def create_next(self):
        """Do nothing"""
        return []


class End(Node):
    """
    End of the flow.

    If no other parallel activities exists, finishes the whole
    process.
    """

    activation_class = EndActivation

    task_type = "END"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event end-event" cx="25" cy="25" r="25"/>
        """,
    }

    bpmn_element = "endEvent"

    def _outgoing(self):
        return iter([])
