from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.template import Template, Context

from .activation import STATUS
from .exceptions import FlowRuntimeError
from .fields import FlowReferenceField, TaskReferenceField, TokenField
from .managers import ProcessManager, TaskManager, coerce_to_related_instance


class AbstractProcess(models.Model):
    """
    Base class for Process data object
    """
    flow_class = FlowReferenceField()
    status = models.CharField(max_length=50, default=STATUS.NEW)

    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True)

    objects = ProcessManager()

    @property
    def created_by(self):
        return self.flow_class.task_class._default_manager \
            .get(process=self, flow_task_type='START').owner

    def active_tasks(self):
        return self.flow_class.task_class._default_manager \
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

        return self.flow_class.task_class._default_manager.get(
            process=self, flow_task=flow_task, status__in=status)

    def summary(self):
        """
        Quick textual process state representation for end user
        """
        if self.flow_class and self.flow_class.process_class == type(self):
            return Template(self.flow_class.summary_template).render(Context({'process': self, 'flow_class': self.flow_class}))

        return "{} - {}".format(self.flow_class.process_title, self.status)

    def __str__(self):
        if self.flow_class:
            return '{} #{}'.format(self.flow_class.process_title, self.pk)
        return "<Process {}> - {}".format(self.pk, self.status)

    def refresh_from_db(self, using=None, fields=None, **kwargs):
        if hasattr(models.Model, 'refresh_from_db'):
            super(AbstractProcess, self).refresh_from_db(using=using, fields=fields, **kwargs)
        else:
            """
            django 1.6, only basic fallback
            """
            db_instance = self.__class__._default_manager.filter(pk=self.pk).get()
            for field in self._meta.concrete_fields:
                setattr(self, field.attname, getattr(db_instance, field.attname))

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

    @property
    def flow_process(self):
        """
        Returns process instance of flow_class type
        """
        if self.flow_task is not None:
            return coerce_to_related_instance(self.process, self.flow_task.flow_class.process_class)

    def summary(self):
        """
        Quick textual task result representation for end user
        """
        if self.flow_task:
            if self.finished:
                if hasattr(self.flow_task, 'task_result_summary'):
                    return Template(self.flow_task.task_result_summary or "").render(Context({
                        'process': self.flow_process,
                        'task': self,
                        'flow_class': self.flow_task.flow_class,
                        'flow_task': self.flow_task}))
            else:
                if hasattr(self.flow_task, 'task_description'):
                    return self.flow_task.task_description or ""

        return ""

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
        activation = self.flow_task.activation_class()
        activation.initialize(self.flow_task, self)
        return activation

    def __str__(self):
        if self.flow_task:
            return "<{}.{}/{}> - {}".format(
                self.flow_task.flow_class._meta.flow_label,
                self.flow_task,
                self.pk,
                self.status)
        return "<Task {}> - {}".format(self.pk, self.status)

    def refresh_from_db(self, using=None, fields=None, **kwargs):
        if hasattr(models.Model, 'refresh_from_db'):
            super(AbstractTask, self).refresh_from_db(using=using, fields=fields, **kwargs)
        else:
            """
            django 1.6, only basic fallback
            """
            db_instance = self.__class__._default_manager.filter(pk=self.pk).get()
            for field in self._meta.concrete_fields:
                setattr(self, field.attname, getattr(db_instance, field.attname))

    class Meta:
        abstract = True


class Process(AbstractProcess):
    class Meta:
        verbose_name_plural = 'Process list'


class Task(AbstractTask):
    process = models.ForeignKey(Process)

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, db_index=True)
    external_task_id = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    owner_permission = models.CharField(max_length=255, blank=True, null=True)

    comments = models.TextField(blank=True, null=True)
