from datetime import datetime
from django.db import models
from viewflow.exceptions import FlowRuntimeError
from viewflow.fields import FlowReferenceField, TaskReferenceField


class Process(models.Model):
    flow_cls = FlowReferenceField()
    created = models.DateTimeField(auto_now_add=True)
    finished = models.DateTimeField(blank=True, null=True)

    def active_tasks(self):
        return Task.objects.filter(process=self, finished__isnull=True).order_by('created')


class Task(models.Model):
    process = models.ForeignKey(Process)
    flow_task = TaskReferenceField(flow_cls_ref='process__flow_cls')

    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(blank=True, null=True)
    finished = models.DateTimeField(blank=True, null=True)

    def get_absolute_url(self):
        if self.process and self.flow_task:
            return self.process.flow_cls.instance.reverse(self)

    def save(self):
        if not self.started:
            self.started = datetime.now()
        super(Task, self).save()


class Activation(Task):
    """
    Proxy class for active task
    """
    def __init__(self, *args, **kwargs):
        self._form = kwargs.pop('form', None)
        super(Activation, self).__init__(*args, **kwargs)

    @property
    def form(self):
        if not self._form:
            raise FlowRuntimeError('No activation from instance set')
        return self._form

    @form.setter
    def form(self, form):
        self._form = form

    class Meta:
        proxy = True


class StartTask(Task):
    """
    Proxy class for initial flow task
    """
    @classmethod
    def from_start_task(cls, start_task):
        """
        initialize new instance from flow start task
        """
        return cls(process=Process(flow_cls=start_task.flow_cls),
                   flow_task=start_task)

    def done(self):
        if not self.process.pk:
            self.process.save()
            self.process_id = self.process.pk
        self.finished = datetime.now()
        self.save()

    class Meta:
        proxy = True
