from datetime import datetime

from django.conf import settings
from django.db import models
from django_fsm import FSMField, transition

from .exceptions import FlowRuntimeError
from .fields import FlowReferenceField, TaskReferenceField, TokenField
from .managers import ProcessManager, TaskManager


class AbstractProcess(models.Model):
    """
    Base class for Process data object
    """
    class STATUS:
        NEW = 'NEW'
        STARTED = 'STR'
        FINISHED = 'FNS'
        ERROR = 'ERR'

    STATUS_CHOICES = ((STATUS.NEW, 'New'),
                      (STATUS.STARTED, 'Stated'),
                      (STATUS.FINISHED, 'Finished'),
                      (STATUS.ERROR, 'Error'))

    flow_cls = FlowReferenceField()
    status = FSMField(max_length=3, choices=STATUS_CHOICES, default=STATUS.NEW)

    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True)

    objects = ProcessManager()

    @transition(field=status, source=STATUS.NEW, target=STATUS.STARTED)
    def start(self):
        pass

    @transition(field=status, source=STATUS.STARTED, target=STATUS.FINISHED)
    def finish(self):
        self.finished = datetime.now()

    @transition(field=status, source=STATUS.STARTED, target=STATUS.ERROR)
    def error(self):
        pass

    @transition(field=status, source=STATUS.ERROR, target=STATUS.STARTED)
    def restart(self):
        pass

    @property
    def created_by(self):
        return self.flow_cls.task_cls._default_manager \
            .get(process=self, flow_task_type='START').owner

    def active_tasks(self):
        return self.flow_cls.task_cls._default_manager \
            .filter(process=self, finished__isnull=True) \
            .order_by('created')

    def get_task(self, flow_task, status=None):
        """
        Return task instance
        """
        if status is None:
            status = [Task.STATUS.NEW, Task.STATUS.ASSIGNED, Task.STATUS.STARTED]
        elif not isinstance(status, (list, tuple)):
            status = [status]

        return self.flow_cls.task_cls._default_manager.get(
            process=self, flow_task=flow_task, status__in=status)

    def __str__(self):
        if self.flow_cls:
            return "<{}/{}> - {}".format(self.flow_cls._meta.namespace, self.pk, self.get_status_display())
        return "<Process {}> - {}".format(self.pk, self.get_status_display())

    class Meta:
        abstract = True


class AbstractTask(models.Model):
    """
    Base class for Task state objects.

    In addition, you have to define at least process foreign key field::

        process = models.ForeignKey(Process)

    """
    class STATUS:
        NEW = 'NEW'
        ASSIGNED = 'ASN'
        PREPARED = 'PRP'
        STARTED = 'STR'
        FINISHED = 'FNS'
        CANCELLED = 'CNC'
        ERROR = 'ERR'

    STATUS_CHOICES = ((STATUS.NEW, 'New'),
                      (STATUS.ASSIGNED, 'Assigned'),
                      (STATUS.PREPARED, 'Prepared for execution'),
                      (STATUS.STARTED, 'Stated'),
                      (STATUS.FINISHED, 'Finished'),
                      (STATUS.CANCELLED, 'Cancelled'),
                      (STATUS.ERROR, 'Error'))

    flow_task = TaskReferenceField()
    flow_task_type = models.CharField(max_length=50)
    status = FSMField(max_length=3, choices=STATUS_CHOICES, default=STATUS.NEW, db_index=True)

    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(blank=True, null=True)
    finished = models.DateTimeField(blank=True, null=True)
    previous = models.ManyToManyField('self')
    token = TokenField(default='start')

    objects = TaskManager()

    def _in_db(self):
        """
        Ensure that we have primary key and that we are safe to create referenced models.
        """
        return self.pk

    @transition(field=status, source=STATUS.NEW, target=STATUS.ASSIGNED)
    def assign(self, *args, **kwargs):
        """
        Tasks that perform some activity should be associated with
        the task owner user or background task id.
        """
        raise NotImplementedError

    @transition(field=status, source=[STATUS.NEW, STATUS.ASSIGNED], target=STATUS.PREPARED)
    def prepare(self):
        """
        Task is going to be started. Task can be initialized several times (probably on GET request).
        Initialized tasks could not be saved.
        """
        self.started = datetime.now()

    @transition(field=status, source=STATUS.PREPARED, target=STATUS.STARTED, conditions=[_in_db])
    def start(self):
        """
        Task that does not involve user view interaction could be marked as started.
        User view task is only prepared but not started, b/c we do not hit db on GET requests.
        """
        pass

    @transition(field=status, source=[STATUS.PREPARED, STATUS.STARTED], target=STATUS.FINISHED)
    def done(self):
        """
        Mark task as done.
        """
        self.finished = datetime.now()

    @transition(field=status, source=[STATUS.ASSIGNED, STATUS.STARTED], target=STATUS.CANCELLED, conditions=[_in_db])
    def cancel(self):
        self.finished = datetime.now()

    @transition(field=status, source=[STATUS.ASSIGNED, STATUS.STARTED], target=STATUS.ERROR, conditions=[_in_db])
    def error(self):
        pass

    def save(self, *args, **kwargs):
        if self.status == Task.STATUS.PREPARED:
            raise FlowRuntimeError("Can't save task with intermediate status - PREPARED")

        if self.flow_task:
            self.flow_task_type = self.flow_task.task_type

        super(AbstractTask, self).save(*args, **kwargs)

    def __str__(self):
        if self.flow_task:
            return "<{}.{}/{}> - {}".format(
                self.flow_task.flow_cls._meta.namespace,
                self.flow_task,
                self.pk,
                self.get_status_display())
        return "<Task {}> - {}".format(self.pk, self.get_status_display())

    class Meta:
        abstract = True


class Process(AbstractProcess):
    class Meta:
        verbose_name_plural = 'Process list'


class Task(AbstractTask):
    process = models.ForeignKey(Process)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, db_index=True)
    external_task_id = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    owner_permission = models.CharField(max_length=50, blank=True, null=True)

    def get_absolute_url(self, user=None, url_type=None):
        if self.process_id and self.flow_task:
            return self.process.flow_cls.instance.get_user_task_url(task=self, user=user)

    @transition(field='status', source=AbstractTask.STATUS.NEW, target=AbstractTask.STATUS.ASSIGNED)
    def assign(self, user=None, external_task_id=None):
        """
        Tasks that perform some activity should be associated with
        the task owner user or background task id.
        """
        self.owner = user
        self.external_task_id = external_task_id
