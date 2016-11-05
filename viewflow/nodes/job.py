from .. import Task, mixins


class AbstractJob(mixins.TaskDescriptionMixin,
                  mixins.NextNodeMixin,
                  mixins.UndoViewMixin,
                  mixins.CancelViewMixin,
                  mixins.DetailViewMixin,
                  Task):
    """
    Base class for task that runs in background.

    Example::

        job = (
            flow.Job(task.job)
            .Next(this.end)
        )
    """

    task_type = 'JOB'

    def __init__(self, job, **kwargs):  # noqa D102
        super(AbstractJob, self).__init__(**kwargs)
        self._job = job

    @property
    def job(self):
        """Callable that should start the job in background."""
        return self._job
