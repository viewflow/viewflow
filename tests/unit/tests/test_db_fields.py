from django.test import TestCase
from viewflow.token import Token
from viewflow.fields import ClassValueWrapper
from ..models import FlowReferencedModel, TokenModel
from ..flows import SingleTaskFlow, AllTaskFlow


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

        second = FlowReferencedModel.objects.get(flow_cls=ClassValueWrapper(SingleTaskFlow))

        self.assertEqual(first.pk, second.pk)

    def test_get_by_flow_task_succeed(self):
        FlowReferencedModel.objects.create(
            flow_cls=SingleTaskFlow, task=SingleTaskFlow.start)
        FlowReferencedModel.objects.create(
            flow_cls=AllTaskFlow, task=AllTaskFlow.start)

        instance = FlowReferencedModel.objects.get(task=SingleTaskFlow.start)

        self.assertEqual(instance.flow_cls, SingleTaskFlow)
        self.assertEqual(instance.task, SingleTaskFlow.start)

    def test_get_by_flow_task_ref_succeed(self):
        FlowReferencedModel.objects.create(
            flow_cls=SingleTaskFlow, task=SingleTaskFlow.start)
        FlowReferencedModel.objects.create(
            flow_cls=AllTaskFlow, task=AllTaskFlow.start)

        instance = FlowReferencedModel.objects.get(task='unit/flows.SingleTaskFlow.start')

        self.assertEqual(instance.flow_cls, SingleTaskFlow)
        self.assertEqual(instance.task, SingleTaskFlow.start)


class TestTokenField(TestCase):
    def test_crud_succeed(self):
        instance = TokenModel()
        instance.token = Token('start/1_2')
        instance.save()

    def test_default_succeed(self):
        instance = TokenModel()
        self.assertTrue(isinstance(instance.token, Token))
        instance.save()

    def test_startswith_lookup_succeed(self):
        TokenModel.objects.create(token='start/1_2')

        instance = TokenModel.objects.get(token__startswith='start/1_')
        self.assertEqual('start/1_2', instance.token)
