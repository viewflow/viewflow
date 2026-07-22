"""Dispatcher for database-backed workflow timers.

Run periodically -- via the ``workflow_timers`` management command from
cron, or a celery beat schedule calling
``viewflow.workflow.tasks.workflow_fire_timers``.
"""

import logging

from django.utils import timezone

from .exceptions import FlowLockFailed
from .models import Task
from .status import STATUS

logger = logging.getLogger(__name__)


def fire_due_timers():
    """Fire every due ``flow.Timer`` task and return the number fired.

    Safe to run from several dispatchers concurrently: each task is
    re-checked under its flow lock, and a task locked by another dispatcher
    is skipped until the next run.

    Flows with a custom task model that is not a proxy of
    ``viewflow.workflow.models.Task`` are not covered.
    """
    fired = 0
    due_tasks = Task._default_manager.filter(
        flow_task_type="TIMER",
        status=STATUS.SCHEDULED,
        scheduled__lte=timezone.now(),
    ).order_by("scheduled")

    for task in due_tasks:
        try:
            with task.activation() as activation:
                start = getattr(activation, "start", None)
                if start is None:
                    # the timer node was renamed or removed since this task
                    # was scheduled; the orphaned row can never fire
                    logger.warning(
                        "Timer task %s references a missing node %r, skipped",
                        task.pk,
                        task.flow_task,
                    )
                    continue
                if start.can_proceed():
                    activation.start()
                    activation.execute()
                    fired += 1
        except FlowLockFailed:
            logger.info(
                "Timer task %s is locked by another dispatcher, skipped", task.pk
            )
        except Exception:  # one broken flow must not block the whole sweep
            logger.exception("Timer task %s failed to fire", task.pk)

    return fired


def fire_due_conditions(flows=None):
    """Fire every armed ``flow.ConditionalCatch`` whose condition now holds.

    Evaluated on the same sweep as ``fire_due_timers``. Each task's condition
    is checked under its flow lock, so a task locked by another dispatcher is
    skipped until the next run. Pass ``flows`` to restrict evaluation to
    specific flow classes.
    """
    fired = 0
    armed = Task._default_manager.filter(flow_task_type="CONDITION", status=STATUS.NEW)

    for task in armed:
        if flows is not None and task.flow_task.flow_class not in flows:
            continue
        try:
            with task.activation() as activation:
                start = getattr(activation, "start", None)
                if start is None:
                    logger.warning(
                        "Conditional task %s references a missing node %r, skipped",
                        task.pk,
                        task.flow_task,
                    )
                    continue
                if start.can_proceed() and activation.condition_met():
                    activation.start()
                    activation.execute()
                    fired += 1
        except FlowLockFailed:
            logger.info(
                "Conditional task %s is locked by another dispatcher, skipped",
                task.pk,
            )
        except Exception:  # one broken flow must not block the whole sweep
            logger.exception("Conditional task %s failed to fire", task.pk)

    return fired


def fire_due_start_timers(flows=None):
    """Start a process for every due ``flow.StartTimer`` and return the count.

    By default discovers flows by importing every installed app's ``flows``
    module; pass ``flows`` to restrict dispatch to specific flow classes.
    Unlike ``fire_due_timers``, there is no process row to lock before the
    first start -- run a single dispatcher instance to avoid duplicates.
    """
    from django.utils.module_loading import autodiscover_modules

    from .base import Flow
    from .checks import _all_flow_subclasses
    from .nodes import StartTimer

    if flows is None:
        autodiscover_modules("flows")
        flows = _all_flow_subclasses(Flow)

    started = 0
    at = timezone.now()
    for flow_class in flows:
        for node in flow_class.instance.nodes():
            if isinstance(node, StartTimer) and node.is_due(at):
                node.run()
                started += 1
    return started
