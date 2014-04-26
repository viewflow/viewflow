from django.db import models

from viewflow.fields import FlowReferenceField, TaskReferenceField, TokenField
from viewflow.models import Process


def default():
    from unit.flows import SingleTaskFlow
    return SingleTaskFlow.start


class FlowReferencedModel(models.Model):
    flow_cls = FlowReferenceField()
    task = TaskReferenceField(default=default)


class TokenModel(models.Model):
    token = TokenField(default='start')


class TestProcess(Process):
    pass
