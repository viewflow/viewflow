from django.db import models
from django.test import TestCase
from viewflow.workflow.fields import FlowReferenceField


class Test(TestCase):
    def test_crud(self):
        obj = TestFlowModel.objects.create(flow_class=Test)
        self.assertEqual(obj.flow_class, Test)

        obj = TestFlowModel.objects.get()
        self.assertEqual(obj.flow_class, Test)

        obj = TestFlowModel.objects.filter(flow_class=Test).first()
        self.assertEqual(obj.flow_class, Test)


class TestFlowModel(models.Model):
    flow_class = FlowReferenceField()
