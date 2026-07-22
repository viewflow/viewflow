"""Compensation throw event.

Runs the compensation handlers registered with ``.CompensateWith`` on
completed tasks, in reverse completion order.
"""

from django.db import transaction
from django.utils.timezone import now

from ..activation import Activation, has_manage_permission
from ..base import Node
from ..signals import task_started
from ..status import STATUS
from . import mixins


class CompensateThrowActivation(mixins.NextNodeActivationMixin, Activation):
    @Activation.status.super()
    def activate(self):
        with self.exception_guard(), transaction.atomic(savepoint=True):
            self.task.started = now()
            task_started.send(
                sender=self.flow_class, process=self.process, task=self.task
            )
            self.run_compensation()

    def run_compensation(self):
        """Run handlers of completed tasks, most recently finished first.

        A task is compensated at most once: hosts that already have a
        handler task linked via ``previous`` are skipped.
        """
        task_class = self.flow_class.task_class
        done_tasks = task_class._default_manager.filter(
            process=self.process, status=STATUS.DONE
        ).order_by("-finished", "-pk")

        for host_task in done_tasks:
            handler = getattr(host_task.flow_task, "_compensation_handler", None)
            if handler is None:
                continue
            already_compensated = (
                task_class._default_manager.filter(
                    flow_task=handler, previous=host_task
                )
                .exclude(status__in=[STATUS.CANCELED, STATUS.REVIVED])
                .exists()
            )
            if already_compensated:
                continue

            prev_activation = host_task.flow_task.activation_class(host_task)
            activation = handler._create(prev_activation, host_task.token)
            activation.activate()
            if activation.complete.can_proceed():
                activation.complete()

    @Activation.status.transition(
        source=[STATUS.ERROR],
        target=STATUS.CANCELED,
        permission=has_manage_permission,
    )
    def cancel(self):
        self.task.finished = now()
        self.task.save()


class CompensateThrow(mixins.NextNodeMixin, Node):
    """
    Compensation throw event: runs the ``.CompensateWith`` handlers of every
    completed task in the process, in reverse completion order, then
    continues.

    Example::

        book_hotel = (
            flow.Function(this.do_book)
            .CompensateWith(this.cancel_hotel)
            .Next(this.pay)
        )
        cancel_hotel = flow.Function(this.do_cancel)
        ...
        compensate = flow.CompensateThrow().Next(this.failed)

    """

    task_type = "EVENT"
    activation_class = CompensateThrowActivation

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event" cx="25" cy="25" r="25" style="stroke-width:4"/>
            <path d="M 24 15 L 14 25 L 24 35 Z M 35 15 L 25 25 L 35 35 Z" fill="rgb(0, 0, 0)" stroke="rgb(0, 0, 0)"/>
        """,
    }

    bpmn_element = "intermediateThrowEvent"

    def bpmn_content(self):
        return "<bpmn:compensateEventDefinition/>"
