from django.test import TestCase
from unit.models import FlowReferencedModel
from unit.flows import SingleTaskFlow


class TestReferenceFields(TestCase):
    """
    Custom db field for store referencies to class
    """
    def test_flowmodel_default_crud_succeed(self):
        instance = FlowReferencedModel()
        instance.flow_cls = SingleTaskFlow
        instance.save()

        instance = FlowReferencedModel.objects.get(pk=instance.pk)
        self.assertEqual(instance.flow_cls, SingleTaskFlow)
        self.assertEqual(instance.task, SingleTaskFlow.start)

    def test_flow_cls_crud_succeed(self):
        instance = FlowReferencedModel.objects.create(
            flow_cls=SingleTaskFlow, task=SingleTaskFlow.end)

        instance = FlowReferencedModel.objects.get(pk=instance.pk)
        self.assertEqual(instance.flow_cls, SingleTaskFlow)
        self.assertEqual(instance.task, SingleTaskFlow.end)

    def test_get_by_cls_succeed(self):
        first = FlowReferencedModel.objects.create(
            flow_cls=SingleTaskFlow, task=SingleTaskFlow.end)

        second = FlowReferencedModel.objects.get(flow_cls=SingleTaskFlow)

        self.assertEqual(first.pk, second.pk)
