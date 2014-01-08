from django.db import models
from viewflow.fields import FlowReferenceField, TaskReferenceField


class Process(models.Model):
    flow_cls = FlowReferenceField()


class Task(models.Model):
    process = models.ForeignKey(Process)
    flow_task = TaskReferenceField(flow_cls_ref='process__flow_cls')

    created = models.DateTimeField(auto_now_add=True)
    started = models.DateTimeField(blank=True, null=True)
    finished = models.DateTimeField(blank=True, null=True)


class ActivationManager(models.Manager):
    pass


class Activation(Task):
    """
    Proxy class for active task
    """
    objects = ActivationManager()

    def done(self):
        pass

    def redirect_to_next():
        pass

    class Meta:
        proxy = True
