from contextlib import contextmanager

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template import Template, Context
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from .fields import FlowReferenceField, TaskReferenceField, TokenField
from .managers import ProcessQuerySet, TaskQuerySet, coerce_to_related_instance
from .token import Token
from . import status


class AbstractProcess(models.Model):
    """Base class for Process data object."""

    flow_class = FlowReferenceField(_("Flow"))
    status = models.CharField(
        _("Status"),
        choices=status.PROCESS.choices,
        default=status.PROCESS.NEW,
        max_length=50,
    )

    created = models.DateTimeField(_("Created"), default=timezone.now)
    finished = models.DateTimeField(_("Finished"), blank=True, null=True)

    objects = ProcessQuerySet.as_manager()

    class Meta:
        abstract = True

    def __str__(self):
        if self.flow_class:
            return "{} #{}".format(self.flow_class.process_title, self.pk)
        return "<Process {}> - {}".format(self.pk, self.status)

    @property
    def brief(self):
        """Quick textual process state representation for end user."""
        template_content = ""

        if self.finished:
            template_content = self.flow_class.process_result_template

        if not template_content:
            template_content = self.flow_class.process_summary_template

        if not template_content:
            template_content = self.flow_class.process_description

        if not template_content:
            template_content = "{{ flow_class.process_title }} - {{ process.status }}"

        return Template(force_str(template_content)).render(
            Context({"process": self.coerced, "flow_class": self.flow_class})
        )

    @property
    def coerced(self):
        """Return process instance of flow_class type."""
        if self.flow_class:
            return coerce_to_related_instance(self, self.flow_class.process_class)
        return self


class AbstractTask(models.Model):
    """
    Base class for Task state objects.

    In addition, you have to define at least process foreign key field::

        process = models.ForeignKey(Process, on_delete=models.CASCADE)

    """

    flow_task = TaskReferenceField(_("Task"))
    flow_task_type = models.CharField(_("Type"), max_length=50)
    status = models.CharField(
        _("Status"),
        choices=status.STATUS.choices,
        db_index=True,
        default=status.STATUS.NEW,
        max_length=50,
    )

    created = models.DateTimeField(_("Created"), default=timezone.now, db_index=True)
    assigned = models.DateTimeField(_("Assigned"), blank=True, null=True)
    started = models.DateTimeField(_("Started"), blank=True, null=True)
    finished = models.DateTimeField(_("Finished"), blank=True, null=True)

    previous = models.ManyToManyField(
        "self", symmetrical=False, related_name="leading", verbose_name=_("Previous")
    )
    token = TokenField(_("Token"), default=Token("start"))

    external_task_id = models.CharField(
        blank=True,
        db_index=True,
        max_length=50,
        null=True,
        verbose_name=_("External Task ID"),
    )

    previous = models.ManyToManyField(
        to="self", symmetrical=False, related_name="leading", verbose_name=_("Previous")
    )

    # permissions
    owner = models.ForeignKey(
        blank=True,
        null=True,
        db_index=True,
        on_delete=models.CASCADE,
        to=settings.AUTH_USER_MODEL,
        verbose_name=_("Owner"),
    )

    owner_permission = models.CharField(
        blank=True,
        max_length=255,
        null=True,
        verbose_name=_("Permission"),
    )

    owner_permission_content_type = models.ForeignKey(
        to=ContentType, on_delete=models.CASCADE, blank=True, null=True
    )

    owner_permission_obj_pk = models.CharField(max_length=255, blank=True, null=True)

    owner_permission_obj = GenericForeignKey(
        "owner_permission_content_type",
        "owner_permission_obj_pk",
        for_concrete_model=False,
    )

    objects = TaskQuerySet.as_manager()

    class Meta:
        abstract = True

    def __str__(self):
        if self.flow_task:
            flow_label = self.flow_task.flow_class.instance.flow_label
            return f"<{flow_label}.{self.flow_task}/{self.pk}> - {self.status}"
        return f"<Task {self.pk}> - {self.status}"

    def save(self, *args, **kwargs):  # noqa D102
        if self.flow_task and not self.flow_task_type:
            self.flow_task_type = self.flow_task.task_type

        super(AbstractTask, self).save(*args, **kwargs)

    @property
    def coerced(self):
        """Return task instance of flow_class type."""
        if self.flow_task is not None:
            return coerce_to_related_instance(
                self, self.flow_task.flow_class.task_class
            )

    @property
    def coerced_process(self):
        """Return process instance of flow_class type."""
        if self.flow_task is not None:
            return coerce_to_related_instance(
                self.process, self.flow_task.flow_class.process_class
            )

    def brief(self):
        """Quick textual task representation for the end user."""
        if not self.flow_task:
            return "< No flow_task assigned >"

        template_content = ""

        if self.finished:
            template_content = self.flow_task.task_result_template

        if not template_content:
            template_content = self.flow_task.task_summary_template

        if not template_content:
            template_content = self.flow_task.task_description

        if not template_content:
            template_content = self.flow_task.task_title

        if not template_content:
            template_content = "{{ flow_task }}/{{ task.status }}"

        return Template(force_str(template_content)).render(
            Context(
                {
                    "process": self.process.coerced,
                    "task": self.coerced,
                    "flow_class": self.flow_task.flow_class,
                    "flow_task": self.flow_task,
                }
            )
        )

    @contextmanager
    def activation(self):
        """
        Context manager for working with task

        with task.activation() as activation:
            pass
        """
        assert self.pk

        with self.flow_task.flow_class.lock(self.process_id):
            self.refresh_from_db()
            yield self.flow_task.activation_class(self)


class Process(AbstractProcess):
    """Default viewflow Process model."""

    data = models.JSONField(null=True, blank=True)

    parent_task = models.ForeignKey(
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="+",
        to="Task",
    )

    # process artifact reference
    artifact = GenericForeignKey("artifact_content_type", "artifact_object_id")

    artifact_content_type = models.ForeignKey(
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="+",
        to=ContentType,
    )
    artifact_object_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:  # noqa D101
        ordering = ["-created"]
        verbose_name = _("Process")
        verbose_name_plural = _("Process list")
        indexes = [
            models.Index(fields=["artifact_content_type", "artifact_object_id"]),
        ]


class Task(AbstractTask):
    """Default viewflow Task model."""

    process = models.ForeignKey(
        on_delete=models.CASCADE,
        to=Process,
        verbose_name=_("Process"),
    )

    data = models.JSONField(null=True, blank=True)

    # task artifact reference
    artifact = GenericForeignKey("artifact_content_type", "artifact_object_id")

    artifact_content_type = models.ForeignKey(
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="+",
        to=ContentType,
    )

    artifact_object_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:  # noqa D101
        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
        ordering = ["-created"]
