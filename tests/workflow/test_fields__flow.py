from django.db import models
from django.test import TestCase
from viewflow.workflow import Flow
from viewflow.workflow.fields import FlowReferenceField


class Test(TestCase):
    def test_crud(self):
        obj = TestFlowModel.objects.create(flow_class=TestFieldsFlow)
        self.assertEqual(obj.flow_class, TestFieldsFlow)

        obj = TestFlowModel.objects.get()
        self.assertEqual(obj.flow_class, TestFieldsFlow)

        obj = TestFlowModel.objects.filter(flow_class=TestFieldsFlow).first()
        self.assertEqual(obj.flow_class, TestFieldsFlow)


class TestFlowModel(models.Model):
    flow_class = FlowReferenceField()


class TestFieldsFlow(Flow):
    pass
