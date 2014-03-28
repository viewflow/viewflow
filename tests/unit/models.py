from django.db import models

from viewflow.fields import FlowReferenceField, TaskReferenceField
from viewflow.models import Process


def default():
    from unit.flows import SingleTaskFlow
    return SingleTaskFlow.start


class FlowReferencedModel(models.Model):
    flow_cls = FlowReferenceField()
    task = TaskReferenceField(default=default)


class TestProcess(Process):
    pass
