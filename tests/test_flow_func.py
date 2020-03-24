try:
    from unittest import mock
except ImportError:
    import mock

from django.test import TestCase
from django.utils.decorators import method_decorator

from viewflow import flow, lock
from viewflow.activation import STATUS, Context
from viewflow.base import this
from viewflow.activation import FuncActivation
from viewflow.nodes.handler import HandlerActivation


class Test(TestCase):
    def init_node(self, node, flow_class=None, name='test_node'):
        node.flow_class = flow_class or FlowStub
        node.name = name
        node.ready()
        return node

    def setUp(self):
        ProcessStub._default_manager.get.return_value = ProcessStub()
        TaskStub._default_manager.get.return_value = TaskStub()
        FlowStub.instance = FlowStub()

    def test_start_function_default(self):
        flow_task = self.init_node(flow.StartFunction())
        act = flow_task.run()
        self.assertEqual(act.task.status, STATUS.DONE)

    def test_start_function_with_default_activation(self):
        @flow.flow_start_func
        def start_func(activation):
            activation.prepare()
            activation.done()
            return activation

        flow_task = self.init_node(flow.StartFunction(start_func))
        act = flow_task.run()
        self.assertEqual(act.task.status, STATUS.DONE)

    def test_start_function_from_flow_method(self):
        class Flow(FlowStub):
            start = flow.StartFunction(this.start_task_func)

            @method_decorator(flow.flow_start_func)
            def start_task_func(self, activation):
                activation.prepare()
                FlowStub.method_called = True
                activation.done()
                return activation

        Flow.instance = Flow()
        flow_task = self.init_node(Flow.start, flow_class=Flow, name='start')

        act = flow_task.run()
        self.assertEqual(act.task.status, STATUS.DONE)
        self.assertTrue(FlowStub.method_called)

    def test_function_activation_lifecycle(self):
        flow_task = self.init_node(flow.Function(lambda t: None))

        act = FuncActivation()
        act.initialize(flow_task, TaskStub())

        # execute
        act.prepare()
        act.done()
        self.assertEqual(act.task.status, STATUS.DONE)

        # undo
        act.undo()
        self.assertEqual(act.task.status, STATUS.NEW)
        act.cancel()
        self.assertEqual(act.task.status, STATUS.CANCELED)

    def test_function_with_default_activation(self):
        @flow.flow_func
        def func_impl(activation):
            activation.prepare()
            activation.done()
            return activation

        flow_task = self.init_node(flow.Function(func_impl, task_loader=lambda flow_task: TaskStub(flow_task)))
        act = flow_task.run()
        self.assertEqual(act.task.status, STATUS.DONE)

    def test_function_from_flow_method(self):
        class Flow(FlowStub):
            func_task = flow.Function(this.task_func, task_loader=lambda flow_task: TaskStub(flow_task))
            method_called = False

            @method_decorator(flow.flow_func)
            def task_func(self, activation):
                activation.prepare()
                FlowStub.method_called = True
                activation.done()
                return activation

        Flow.instance = Flow()
        flow_task = self.init_node(Flow.func_task, flow_class=Flow, name='task')

        act = flow_task.run()
        self.assertEqual(act.task.status, STATUS.DONE)
        self.assertTrue(FlowStub.method_called)

    def test_handler_activation_lifecycle(self):
        def handler(activation):
            pass

        flow_task = self.init_node(flow.Handler(handler))

        act = HandlerActivation()
        act.initialize(flow_task, TaskStub())

        # execute
        act.perform()
        self.assertEqual(act.task.status, STATUS.DONE)

        # undo
        act.undo()
        self.assertEqual(act.task.status, STATUS.NEW)
        act.cancel()
        self.assertEqual(act.task.status, STATUS.CANCELED)

    def test_handler_activation_error_lifecycle(self):
        def handler(activation):
            raise ValueError('expected')

        flow_task = self.init_node(flow.Handler(handler))

        act = HandlerActivation()
        act.initialize(flow_task, TaskStub())

        # by default errors are propogated
        self.assertRaises(ValueError, act.perform)

        # disable gate error propagation
        with Context(propagate_exception=False):
            act.perform()
            self.assertEqual(act.task.status, STATUS.ERROR)

            act.retry()
            self.assertEqual(act.task.status, STATUS.ERROR)

        # undo
        act.undo()
        self.assertEqual(act.task.status, STATUS.NEW)
        act.cancel()
        self.assertEqual(act.task.status, STATUS.CANCELED)

    def test_handler_from_flow_method(self):
        class Flow(FlowStub):
            handler_task = flow.Handler(this.task_handler)
            method_called = False

            def task_handler(self, activation):
                Flow.method_called = True

        Flow.instance = Flow()
        flow_task = self.init_node(Flow.handler_task, flow_class=Flow, name='task')

        act = HandlerActivation()
        act.initialize(flow_task, TaskStub())

        # execute
        act.perform()
        self.assertEqual(act.task.status, STATUS.DONE)
        self.assertEqual(act.task.status, STATUS.DONE)
        self.assertTrue(Flow.method_called)


class ProcessStub(object):
    _default_manager = mock.Mock()

    def __init__(self, flow_class=None):
        self.flow_class = flow_class

    def active_tasks(self):
        return []

    def save(self):
        self.pk = 1
        return


class TaskStub(object):
    _default_manager = mock.Mock()

    def __init__(self, flow_task=None):
        self.flow_task = flow_task
        self.process_id = 1
        self.pk = 1
        self.status = STATUS.NEW
        self.started = None

    @property
    def leading(self):
        from viewflow.models import Task
        return Task.objects.none()

    def save(self):
        self.pk = 1
        return


class FlowStub(object):
    process_class = ProcessStub
    task_class = TaskStub
    lock_impl = lock.no_lock
    instance = None


class UserStub(object):
    pass
