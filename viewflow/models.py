from datetime import datetime
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

    def save(self):
        if not self.started:
            self.started = datetime.now()
        super(Task, self).save()


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
