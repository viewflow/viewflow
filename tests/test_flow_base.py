from textwrap import dedent

from django.test import TestCase
from django.contrib.auth.models import User

from viewflow import flow
from viewflow.base import Flow
from viewflow.activation import STATUS
from viewflow.base import This, Node
from viewflow.models import Process
from viewflow.mixins import PermissionMixin, TaskDescriptionViewMixin


class Test(TestCase):
    def test_this_refs(self):
        this = This()

        self.assertEqual(this.some_name.name, 'some_name')
        self.assertEqual(this.another_some_name.name, 'another_some_name')

    def test_this_owner(self):
        this = This()
        user = User.objects.create(username='testowner')
        process = TestFlowBaseFlow.process_class.objects.create(flow_class=TestFlowBaseFlow)

        task = TestFlowBaseFlow.task_class.objects.create(
            process=process, flow_task=TestFlowBaseFlow.start,
            owner=user, status=STATUS.DONE)

        self.assertEqual(this.start.owner(task.activate()), user)

    def test_permission_mixin_creation(self):
        class TestNode(PermissionMixin, Node):
            pass

        flow_task = TestNode().Permission(auto_create=True)
        flow_task.name = "test_task"
        flow_task.flow_class = TestFlowBaseFlow
        flow_task.ready()

        self.assertIn(('can_test_task_testflowbaseprocess', 'Can test task'),
                      TestFlowBaseFlow.process_class._meta.permissions)

    def test_task_description_mixin_parse(self):
        class TestView(object):
            """
            Test Task

            Docstrings from views are extracted to be a documentation
            for the task node
            """
            task_result_summary = "Summary for the completed task"

        class TestNode(TaskDescriptionViewMixin, Node):
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
    process_class = TestFlowBaseProcess
    start = flow.Start(lambda request: None)
