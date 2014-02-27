from django.db import models

from viewflow.fields import FlowReferenceField, TaskReferenceField
from unit.flows import SingleTaskFlow


class FlowReferencedModel(models.Model):
    flow_cls = FlowReferenceField()
    task = TaskReferenceField(flow_cls_ref='flow_cls', default=SingleTaskFlow.start)

