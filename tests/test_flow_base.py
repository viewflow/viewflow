from textwrap import dedent

from django.test import TestCase
from django.contrib.auth.models import User

from viewflow import flow
from viewflow.base import Flow
from viewflow.activation import STATUS
from viewflow.flow import base
from viewflow.models import Process


class Test(TestCase):
    def test_this_refs(self):
        this = base.This()

        self.assertEqual(this.some_name.name, 'some_name')
        self.assertEqual(this.another_some_name.name, 'another_some_name')

    def test_this_owner(self):
        this = base.This()
        user = User.objects.create(username='testowner')
        process = TestFlowBaseFlow.process_cls.objects.create(flow_cls=TestFlowBaseFlow)

        TestFlowBaseFlow.task_cls.objects.create(
            process=process, flow_task=TestFlowBaseFlow.start,
            owner=user, status=STATUS.DONE)  # TODO allow any non cancelled status

        self.assertEqual(this.start.owner(process), user)

    def test_permission_mixin_creation(self):
        class TestNode(base.PermissionMixin, base.Node):
            pass

        flow_task = TestNode().Permission(auto_create=True)
        flow_task.name = "test_task"
        flow_task.flow_cls = TestFlowBaseFlow
        flow_task.ready()

        self.assertIn(('can_test_task_testflowbaseprocess', 'Can test task'),
                      TestFlowBaseFlow.process_cls._meta.permissions)

    def test_task_description_mixin_parse(self):
        class TestView(object):
            """
            Test Task

            Docstrings from views are extracted to be a documentation
            for the task node
            """
            task_result_summary = "Summary for the completed task"

        class TestNode(base.TaskDescriptionViewMixin, base.Node):
            pass

        flow_task = TestNode(TestView)
        self.assertEqual(flow_task.task_title, 'Test Task')
        self.assertEqual(flow_task.task_description, dedent('''
            Docstrings from views are extracted to be a documentation
            for the task node''').strip())
        self.assertEqual(flow_task.task_result_summary, 'Summary for the completed task')

    def test_task_description_mixin_kwargs(self):
        flow_task = flow.End(
            task_title='Test Task',
            task_description='Task Description',
            task_result_summary='Summary for the completed task')

        self.assertEqual(flow_task.task_title, 'Test Task')
        self.assertEqual(flow_task.task_description, 'Task Description')
        self.assertEqual(flow_task.task_result_summary, 'Summary for the completed task')


class TestFlowBaseProcess(Process):
    pass


class TestFlowBaseFlow(Flow):
    process_cls = TestFlowBaseProcess
    start = flow.Start(lambda request: None)
