from django.conf import settings
from django.db import models

from .activation import STATUS
from .exceptions import FlowRuntimeError
from .fields import FlowReferenceField, TaskReferenceField, TokenField
from .managers import ProcessManager, TaskManager


class AbstractProcess(models.Model):
    """
    Base class for Process data object
    """
    flow_cls = FlowReferenceField()
    status = models.CharField(max_length=50, default=STATUS.NEW)

    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True)

    objects = ProcessManager()

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
            status = [STATUS.NEW, STATUS.ASSIGNED, STATUS.STARTED]
        elif not isinstance(status, (list, tuple)):
            status = [status]

        return self.flow_cls.task_cls._default_manager.get(
            process=self, flow_task=flow_task, status__in=status)

    def __str__(self):
        if self.flow_cls:
            return "<{}/{}> - {}".format(self.flow_cls._meta.namespace, self.pk, self.status)
        return "<Process {}> - {}".format(self.pk, self.status)

    class Meta:
        abstract = True


class AbstractTask(models.Model):
    """
    Base class for Task state objects.

    In addition, you have to define at least process foreign key field::

        process = models.ForeignKey(Process)

    """
    flow_task = TaskReferenceField()
    flow_task_type = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default=STATUS.NEW, db_index=True)

    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(blank=True, null=True)
    finished = models.DateTimeField(blank=True, null=True)
    previous = models.ManyToManyField('self', symmetrical=False, related_name='leading')
    token = TokenField(default='start')

    objects = TaskManager()

    def save(self, *args, **kwargs):
        if self.status == STATUS.PREPARED:
            raise FlowRuntimeError("Can't save task with intermediate status - PREPARED")

        if self.flow_task:
            self.flow_task_type = self.flow_task.task_type

        super(AbstractTask, self).save(*args, **kwargs)

    def activate(self):
        """
        Instantiate and configure new task activation
        """
        activation = self.flow_task.activation_cls()
        activation.initialize(self.flow_task, self)
        return activation

    def __str__(self):
        if self.flow_task:
            return "<{}.{}/{}> - {}".format(
                self.flow_task.flow_cls._meta.namespace,
                self.flow_task,
                self.pk,
                self.status)
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

    comments = models.TextField(blank=True, null=True)
