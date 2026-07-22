from datetime import datetime, timedelta

from django.db import transaction
from django.utils.timezone import now

from viewflow import this

from ..activation import Activation, has_manage_permission
from ..base import Node
from ..context import Context
from ..status import STATUS
from . import mixins
from .start import StartHandle


class TimerActivation(mixins.NextNodeActivationMixin, Activation):
    """Activation for the database-backed Timer node."""

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.SCHEDULED)
    def activate(self):
        """Store the due moment on the task row for the timer dispatcher."""
        with self.exception_guard(), transaction.atomic(savepoint=True):
            delay = self.flow_task._delay
            if callable(delay):
                delay = delay(self)
            if isinstance(delay, timedelta):
                delay = now() + delay
            if not isinstance(delay, datetime):
                raise ValueError(
                    f"Timer delay must be a timedelta or datetime, got {delay!r}"
                )
            self.task.scheduled = delay
            self.task.save()

    @Activation.status.transition(source=STATUS.SCHEDULED, target=STATUS.STARTED)
    def start(self):
        """Claim the due timer; called by the timer dispatcher."""
        self.task.started = now()
        self.task.save()

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.DONE)
    def complete(self):
        super().complete.original()

    @Activation.status.transition(source=STATUS.STARTED)
    def execute(self):
        """Fire the timer and continue the process.

        Runs in the background dispatcher, so a failure downstream is
        recorded as a task ERROR instead of propagating.
        """
        self.complete()
        with Context(propagate_exception=False):
            self.activate_next()

    @Activation.status.transition(
        source=[STATUS.NEW, STATUS.SCHEDULED],
        target=STATUS.CANCELED,
        permission=has_manage_permission,
    )
    def cancel(self):
        self.task.finished = now()
        self.task.save()


class Timer(mixins.NextNodeMixin, Node):
    """
    Wait until a specified moment, stored in the database.

    Unlike ``viewflow.contrib.celery.Timer``, the due moment survives a
    message broker flush. Due timers are fired by the dispatcher --
    the ``workflow_timers`` management command, run periodically::

        class MyFlow(flow.Flow):
            ...
            wait = flow.Timer(timedelta(days=1)).Next(this.escalate)
            ...

    :param delay: ``timedelta`` from activation, an absolute ``datetime``,
        or a callable ``activation -> timedelta | datetime``.
    """

    activation_class = TimerActivation

    task_type = "TIMER"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <ellipse cx="25" cy="25" rx="19.5" ry="19.5" fill="rgb(255, 255, 255)" stroke="rgb(0, 0, 0)"/>
            <path d="M 25 5.5 L 25 8 M 34.69 8.05 L 33.29 10.5 M 41.77 15.14 L 39.32 16.63 M 44.5 25 L 41.92 25 M 41.77 34.79 L 39.32 33.29 M 34.69 41.87 L 33.29 39.43 M 25 41.92 L 25 44.5 M 15.23 41.87 L 16.63 39.43 M 8.15 34.79 L 10.6 33.29 M 5.5 25 L 8 25 M 8.15 15.14 L 10.6 16.63 M 15.23 8.05 L 16.63 10.5 M 25.96 8.25 L 25 25 L 35.94 25.46" fill="none" stroke="rgb(0, 0, 0)" stroke-miterlimit="10"/>
            <circle class="event" cx="25" cy="25" r="25"/>
        """,
    }

    bpmn_element = "intermediateCatchEvent"

    def __init__(self, delay, **kwargs):
        super().__init__(**kwargs)
        self._delay = delay

    def _resolve(self, instance):
        super()._resolve(instance)
        self._delay = this.resolve(instance, self._delay)

    def bpmn_content(self):
        delay = self._delay
        if isinstance(delay, timedelta):
            return (
                "<bpmn:timerEventDefinition><bpmn:timeDuration>"
                f"PT{int(delay.total_seconds())}S"
                "</bpmn:timeDuration></bpmn:timerEventDefinition>"
            )
        if isinstance(delay, datetime):
            return (
                "<bpmn:timerEventDefinition><bpmn:timeDate>"
                f"{delay.isoformat()}"
                "</bpmn:timeDate></bpmn:timerEventDefinition>"
            )
        return "<bpmn:timerEventDefinition/>"


class StartTimer(StartHandle):
    """
    Start a new process on a schedule.

    Due start timers are fired by the periodic ``workflow_timers``
    dispatcher. The first process starts on the first dispatcher run,
    subsequent ones an ``interval`` after the previous start. Run a single
    dispatcher instance to avoid duplicate starts.

    For cron-style schedules, point celery beat or OS cron directly at
    ``MyFlow.start.run()`` instead.

    Example::

        class ReportFlow(flow.Flow):
            start = flow.StartTimer(interval=timedelta(days=1)).Next(this.report)
            ...

    :param interval: ``timedelta`` between process starts.
    """

    def __init__(self, interval=None, **kwargs):
        if interval is None:
            raise ValueError("StartTimer requires an interval")
        super().__init__(**kwargs)
        self._interval = interval

    def last_run(self):
        """Creation moment of the latest start task for this node, if any."""
        task = (
            self.flow_class.task_class._default_manager.filter(flow_task=self)
            .order_by("-created")
            .first()
        )
        return task.created if task is not None else None

    def is_due(self, at):
        last_run = self.last_run()
        return last_run is None or last_run + self._interval <= at

    def bpmn_content(self):
        seconds = int(self._interval.total_seconds())
        return (
            "<bpmn:timerEventDefinition><bpmn:timeCycle>"
            f"R/PT{seconds}S"
            "</bpmn:timeCycle></bpmn:timerEventDefinition>"
        )
