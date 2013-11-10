from django.db import models
from viewflow.fields import ClassReferenceField


class Process(models.Model):
    flow_cls = ClassReferenceField()


class Task(models.Model):
    process = models.ForeignKey(Process)


class Activation(Task):
    """
    Proxy class for active task
    """
    def done(self):
        pass

    def redirect_to_next():
        pass

    class Meta:
        proxy = True
