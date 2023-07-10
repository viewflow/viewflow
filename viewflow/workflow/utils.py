from .status import STATUS


class Act(object):
    """Shortcut to access activation data."""

    @property
    def process(self):
        """Shortcut for lambda activation: activation.process...)"""

        class Lookup(object):
            def __getattribute__(self, name):
                return lambda activation: getattr(activation.process, name)

        return Lookup()

    @property
    def task(self):
        """Shortcut for lambda activation: activation.task...)"""

        class Lookup(object):
            def __getattribute__(self, name):
                return lambda activation: getattr(activation.task, name)

        return Lookup()


act = Act()


def get_next_process_task(manager, process, user):
    task = manager.filter(process=process, owner=user, status=STATUS.ASSIGNED).first()

    # lookup for a task in a queue
    if task is None:
        task = (
            manager.user_queue(user).filter(process=process, status=STATUS.NEW).first()
        )

    # lookup for a job
    if task is None:
        task = manager.filter(
            process=process,
            flow_task_type="JOB",
            status__in=[STATUS.NEW, STATUS.SCHEDULED, STATUS.STARTED],
        ).first()

    return task
