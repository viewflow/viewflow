from django.test import TestCase

from viewflow import fields, flow
from viewflow.base import Flow, this
from viewflow.token import Token


class Test(TestCase):
    def test_import_flow_by_ref_succeed(self):
        flow_class = fields.import_flow_by_ref('viewflow/base.Flow')
        self.assertTrue(issubclass(flow_class, Flow))

        flow_class = fields.import_flow_by_ref('tests/test_fields.TestFlow')
        self.assertTrue(flow_class is TestFlow)

    def test_get_flow_ref_succeed(self):
        self.assertEqual(fields.get_flow_ref(Flow), 'viewflow/base.Flow')
        self.assertEqual(fields.get_flow_ref(TestFlow), 'tests/test_fields.TestFlow')

    def test_import_task_by_ref_succeed(self):
        self.assertEqual(fields.import_task_by_ref('tests/test_fields.TestFlow.start'), TestFlow.start)
        self.assertEqual(fields.import_task_by_ref('tests/test_fields.TestFlow.end'), TestFlow.end)

    def test_get_task_ref_succeed(self):
        self.assertEqual(fields.get_task_ref(TestFlow.start), 'tests/test_fields.TestFlow.start')
        self.assertEqual(fields.get_task_ref(TestFlow.end), 'tests/test_fields.TestFlow.end')

    def test_flow_reference_field_prep_value_succeed(self):
        field = fields.FlowReferenceField()

        self.assertEqual(field.get_prep_value(None), None)
        self.assertEqual(field.get_prep_value(''), '')
        self.assertEqual(field.get_prep_value('tests/test_fields.TestFlow'), 'tests/test_fields.TestFlow')
        self.assertEqual(field.get_prep_value(TestFlow), 'tests/test_fields.TestFlow')

    def test_flow_reference_field_to_python_succeed(self):
        field = fields.FlowReferenceField()

        self.assertEqual(field.to_python(None), None)
        self.assertEqual(field.to_python(''), '')  # TODO Fix it
        self.assertEqual(field.to_python(TestFlow), TestFlow)
        self.assertEqual(field.to_python('tests/test_fields.TestFlow'), TestFlow)

    def test_task_reference_field_prep_value_succeed(self):
        field = fields.TaskReferenceField()

        self.assertEqual(field.get_prep_value(None), None)
        self.assertEqual(field.get_prep_value(''), '')
        self.assertEqual(field.get_prep_value('tests/test_fields.TestFlow.start'), 'tests/test_fields.TestFlow.start')
        self.assertEqual(field.get_prep_value(TestFlow.start), 'tests/test_fields.TestFlow.start')

    def test_task_reference_field_to_python_succeed(self):
        field = fields.TaskReferenceField()

        self.assertEqual(field.to_python(None), None)
        self.assertEqual(field.to_python(''), '')  # TODO Fix it
        self.assertEqual(field.to_python(TestFlow.start), TestFlow.start)
        self.assertEqual(field.to_python('tests/test_fields.TestFlow.start'), TestFlow.start)

    def test_token_field_prep_value_succeed(self):
        field = fields.TokenField()

        self.assertEqual(field.get_prep_value(None), None)
        self.assertEqual(field.get_prep_value(''), '')
        self.assertEqual(field.get_prep_value('start/1'), 'start/1')
        self.assertEqual(field.get_prep_value(Token('start/1')), 'start/1')

    def test_token_field_to_python_succeed(self):
        field = fields.TokenField()

        self.assertEqual(field.to_python(None), None)
        self.assertEqual(field.to_python(''), '')  # TODO Fix it
        self.assertEqual(field.to_python(Token('start/1')), Token('start/1'))
        self.assertEqual(field.to_python('start/1'), Token('start/1'))


class TestFlow(Flow):
    start = flow.Start(lambda request: None).Next(this.end)
    end = flow.End()
