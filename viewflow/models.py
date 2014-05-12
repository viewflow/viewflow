from datetime import datetime

from django.conf import settings
from django.db import models
from django_fsm import FSMField, transition

from viewflow.exceptions import FlowRuntimeError
from viewflow.fields import FlowReferenceField, TaskReferenceField, TokenField


class Process(models.Model):
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

    def active_tasks(self):
        return Task.objects.filter(process=self, finished__isnull=True).order_by('created')

    def __str__(self):
        if self.flow_cls:
            return "<{}/{}> - {}".format(self.flow_cls._meta.namespace, self.pk, self.get_status_display())
        return "<Process {}> - {}".format(self.pk, self.get_status_display())

    class Meta:
        verbose_name_plural = 'Process list'


class Task(models.Model):
    """
    Base class for Task state objects
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

    process = models.ForeignKey(Process)
    flow_task = TaskReferenceField()
    flow_task_type = models.CharField(max_length=50)
    status = FSMField(max_length=3, choices=STATUS_CHOICES, default=STATUS.NEW)

    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(blank=True, null=True)
    finished = models.DateTimeField(blank=True, null=True)
    previous = models.ManyToManyField('self')
    token = TokenField(default='start')

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    external_task_id = models.CharField(max_length=50, blank=True, null=True)

    owner_permission = models.CharField(max_length=50, blank=True, null=True)

    def _in_db(self):
        """
        Ensure that we have primary key and that we are safe to create referenced models.
        """
        return self.pk

    @transition(field=status, source=STATUS.NEW, target=STATUS.ASSIGNED, conditions=[_in_db])
    def assign(self, user=None, external_task_id=None):
        """
        Tasks that perform some activity should be associated with
        the task owner user or background task id.
        """
        self.owner = user
        self.external_task_id = external_task_id

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

    def get_absolute_url(self):
        if self.process and self.flow_task:
            return self.process.flow_cls.instance.reverse(self)

    def save(self, *args, **kwargs):
        if self.status == Task.STATUS.PREPARED:
            raise FlowRuntimeError("Can't save task with intermediate status - PREPARED")

        if self.flow_task:
            self.flow_task_type = self.flow_task.task_type

        super(Task, self).save(*args, **kwargs)

    def __str__(self):
        if self.flow_task:
            return "<{}.{}/{}> - {}".format(
                self.flow_task.flow_cls._meta.namespace,
                self.flow_task,
                self.pk,
                self.get_status_display())
        return "<Task {}> - {}".format(self.pk, self.get_status_display())
