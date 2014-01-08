from django.db import models
from django.test import TestCase

from viewflow import flow, Flow
from viewflow.fields import FlowReferenceField, TaskReferenceField


def perform_task(request, act_id):
    raise NotImplementedError


class TestFlow(Flow):
    start = flow.Start() \
        .Activate('task')
    task = flow.View(perform_task)\
        .Next('end')
    end = flow.End()


class TestFlowConformance(TestCase):
    """
    Basic flow class API
    """
    def test_flow_meta_creation_succeed(self):
        self.assertTrue(hasattr(TestFlow, '_meta'))

    def test_task_names_established(self):
        names = set(node.name for node in TestFlow._meta.nodes())
        self.assertEqual(set(['start', 'task', 'end']), names)

    def test_flow_interlinks_resolved(self):
        for node in TestFlow._meta.nodes():
            for edge in node._outgoing():
                self.assertTrue(isinstance(edge.dst, flow._Node))
            for edge in node._incoming():
                self.assertTrue(isinstance(edge.dst, flow._Node))


class TestFlowAdmin(TestCase):
    """
    Flow admin
    """
    pass


class FlowReferencedModel(models.Model):
    flow_cls = FlowReferenceField()
    task = TaskReferenceField(flow_cls_ref='flow_cls', default=TestFlow.start)


class TestReferenceFields(TestCase):
    """
    Custom db field for store referencies to class
    """
    def test_flowmodel_default_crud_succeed(self):
        instance = FlowReferencedModel()
        instance.flow_cls = TestFlow
        instance.save()

        instance = FlowReferencedModel.objects.get(pk=instance.pk)
        self.assertEqual(instance.flow_cls, TestFlow)
        self.assertEqual(instance.task, TestFlow.start)

    def test_flow_cls_crud_succeed(self):
        instance = FlowReferencedModel.objects.create(
            flow_cls=TestFlow, task=TestFlow.end)
        instance = FlowReferencedModel.objects.get(pk=instance.pk)
        self.assertEqual(instance.flow_cls, TestFlow)
        self.assertEqual(instance.task, TestFlow.end)
