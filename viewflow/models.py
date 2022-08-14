from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template import Template, Context
from django.utils.encoding import force_str
from jsonstore import JSONField

from .activation import STATUS, STATUS_CHOICES
from .compat import _
from .exceptions import FlowRuntimeError
from .fields import FlowReferenceField, TaskReferenceField, TokenField
from .managers import ProcessQuerySet, TaskQuerySet, coerce_to_related_instance

try:
    from django.utils.encoding import python_2_unicode_compatible
except ImportError:
    # django 3.0+
    python_2_unicode_compatible = lambda cls: cls  # NOQA


@python_2_unicode_compatible
class AbstractProcess(models.Model):
    """Base class for Process data object."""

    flow_class = FlowReferenceField(_('Flow'))
    status = models.CharField(_('Status'), max_length=50, default=STATUS.NEW)

    created = models.DateTimeField(_('Created'), auto_now_add=True)
    finished = models.DateTimeField(_('Finished'), blank=True, null=True)

    objects = ProcessQuerySet.as_manager()

    @property
    def created_by(self):
        """Lookup for the owner of the task that started the flow."""
        return self.flow_class.task_class._default_manager \
            .get(process=self, flow_task_type='START').owner

    def active_tasks(self):
        """List of non finished tasks."""
        return self.flow_class.task_class._default_manager \
            .filter(process=self, finished__isnull=True) \
            .order_by('created')

    def get_task(self, flow_task, status=None):
        """Lookup for task instance in the db."""
        if status is None:
            status = [STATUS.NEW, STATUS.ASSIGNED, STATUS.STARTED]
        elif not isinstance(status, (list, tuple)):
            status = [status]

        return self.flow_class.task_class._default_manager.get(
            process=self, flow_task=flow_task, status__in=status)

    def summary(self):
        """Quick textual process state representation for end user."""
        if self.flow_class and self.flow_class.process_class == type(self):
            return Template(
                force_str(self.flow_class.summary_template)
            ).render(
                Context({'process': self, 'flow_class': self.flow_class})
            )

        return f"{self.flow_class.process_title} - {self.status}"

    def __str__(self):
        if self.flow_class:
            return f'{self.flow_class.process_title} #{self.pk}'
        return f"<Process {self.pk}> - {self.status}"

    class Meta:  # noqa D101
        abstract = True


@python_2_unicode_compatible
class AbstractTask(models.Model):
    """
    Base class for Task state objects.

    In addition, you have to define at least process foreign key field::

        process = models.ForeignKey(Process, on_delete=models.CASCADE)

    """

    flow_task = TaskReferenceField(_('Task'))
    flow_task_type = models.CharField(_('Type'), max_length=50)
    status = models.CharField(_('Status'), max_length=50, default=STATUS.NEW, db_index=True)

    created = models.DateTimeField(_('Created'), auto_now_add=True)
    assigned = models.DateTimeField(_('Assigned'), blank=True, null=True)
    started = models.DateTimeField(_('Started'), blank=True, null=True)
    finished = models.DateTimeField(_('Finished'), blank=True, null=True)
    previous = models.ManyToManyField('self', symmetrical=False, related_name='leading', verbose_name=_('Previous'))
    token = TokenField(_('Token'), default='start')

    objects = TaskQuerySet.as_manager()

    def get_status_display(self):
        return dict(STATUS_CHOICES).get(self.status, self.status)

    @property
    def flow_process(self):
        """Return process instance of flow_class type."""
        if self.flow_task is not None:
            return coerce_to_related_instance(self.process, self.flow_task.flow_class.process_class)

    def summary(self):
        """Quick textual task result representation for end user."""
        if self.flow_task:
            if self.finished:
                if hasattr(self.flow_task, 'task_result_summary'):
                    return Template(force_str(self.flow_task.task_result_summary or "")).render(Context({
                        'process': self.flow_process,
                        'task': self,
                        'flow_class': self.flow_task.flow_class,
                        'flow_task': self.flow_task}))
            else:
                if hasattr(self.flow_task, 'task_description'):
                    return Template(force_str(self.flow_task.task_description or "")).render(Context({
                        'process': self.flow_process,
                        'task': self,
                        'flow_class': self.flow_task.flow_class,
                        'flow_task': self.flow_task}))

        return ""

    def save(self, *args, **kwargs):  # noqa D102
        if self.status == STATUS.PREPARED:
            raise FlowRuntimeError("Can't save task with intermediate status - PREPARED")

        if self.flow_task:
            self.flow_task_type = self.flow_task.task_type

        super().save(*args, **kwargs)

    def activate(self):
        """Instantiate and configure new task activation."""
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
        return f"<Task {self.pk}> - {self.status}"

    class Meta:  # noqa D101
        abstract = True


class Process(AbstractProcess):
    """Default viewflow Process model."""
    artifact_content_type = models.ForeignKey(
        ContentType, null=True, blank=True,
        on_delete=models.CASCADE, related_name='+')
    artifact_object_id = models.PositiveIntegerField(null=True, blank=True)
    artifact = GenericForeignKey('artifact_content_type', 'artifact_object_id')

    data = JSONField(null=True, blank=True)

    class Meta:  # noqa D101
        ordering = ['-created']
        verbose_name = _('Process')
        verbose_name_plural = _('Process list')


class Task(AbstractTask):
    """Default viewflow Task model."""

    process = models.ForeignKey(Process, on_delete=models.CASCADE, verbose_name=_('Process'))

    artifact_content_type = models.ForeignKey(
        ContentType, null=True, blank=True,
        on_delete=models.CASCADE, related_name='+'
    )
    artifact_object_id = models.PositiveIntegerField(null=True, blank=True)
    artifact = GenericForeignKey('artifact_content_type', 'artifact_object_id')

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, db_index=True,
        on_delete=models.CASCADE, verbose_name=_('Owner'))
    external_task_id = models.CharField(_('External Task ID'), max_length=50, blank=True, null=True, db_index=True)
    owner_permission = models.CharField(_('Permission'), max_length=255, blank=True, null=True)
    comments = models.TextField(_('Comments'), blank=True, null=True)

    data = JSONField(null=True, blank=True)


    class Meta:  # noqa D101
        verbose_name = _('Task')
        verbose_name_plural = _('Tasks')
        ordering = ['-created']
