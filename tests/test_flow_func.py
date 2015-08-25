from django.test import TestCase
from django.utils.decorators import method_decorator

from viewflow import flow, lock
from viewflow.activation import STATUS, StartActivation, Activation, Context
from viewflow.compat import mock
from viewflow.flow import func


class Test(TestCase):
    def init_node(self, node, flow_cls=None, name='test_node'):
        node.flow_cls = flow_cls or FlowStub
        node.name = name
        return node

    def setUp(self):
        ProcessStub._default_manager.get.return_value = ProcessStub()
        TaskStub._default_manager.get.return_value = TaskStub()
        FlowStub.instance = FlowStub()

    def test_start_function_default(self):
        flow_task = self.init_node(flow.StartFunction())
        act = flow_task.run()
        self.assertEqual(act.task.status, STATUS.DONE)

    def test_start_function_inline_activation(self):
        class StartFunc(StartActivation):
            inline_called = False

            @Activation.status.super()
            def initialize(self, flow_task, task):
                StartFunc.inline_called = True
                super(StartFunc, self).initialize(flow_task, task)

            def __call__(self):
                self.prepare()
                self.done()
                return self

        flow_task = self.init_node(flow.StartFunction(StartFunc))
        act = flow_task.run()
        self.assertEqual(act.task.status, STATUS.DONE)
        self.assertTrue(StartFunc.inline_called)

    def test_start_function_with_default_activation(self):
        def start_func(activation):
            activation.prepare()
            activation.done()
            return activation

        flow_task = self.init_node(flow.StartFunction(start_func))
        act = flow_task.run()
        self.assertEqual(act.task.status, STATUS.DONE)

    def test_start_function_from_flow_method(self):
        class Flow(FlowStub):
            start = flow.StartFunction()

            def start_task_func(self, activation):
                activation.prepare()
                FlowStub.method_called = True
                activation.done()
                return activation

        Flow.instance = Flow()
        flow_task = self.init_node(Flow.start, flow_cls=Flow, name='start')

        act = flow_task.run()
        self.assertEqual(act.task.status, STATUS.DONE)
        self.assertTrue(FlowStub.method_called)

    def test_function_activation_lifecycle(self):
        flow_task = self.init_node(flow.Function())

        act = func.FuncActivation()
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

    def test_function_inline_activation(self):
        class Func(func.FuncActivation, func.FlowFunc):
            inline_called = False

            def get_task(self, flow_task, *func_args, **func_kwars):
                return TaskStub()

            @Activation.status.super()
            def initialize(self, flow_task, task):
                Func.inline_called = True
                super(Func, self).initialize(flow_task, task)

            def __call__(self):
                self.prepare()
                self.done()
                return self

    def test_function_with_default_activation(self):
        @flow.flow_func(task_loader=lambda flow_task: TaskStub())
        def func_impl(activation):
            activation.prepare()
            activation.done()
            return activation

        flow_task = self.init_node(flow.Function(func_impl))
        act = flow_task.run()
        self.assertEqual(act.task.status, STATUS.DONE)

    def test_function_from_flow_method(self):
        class Flow(FlowStub):
            func_task = flow.Function()
            method_called = False

            @method_decorator(flow.flow_func(task_loader=lambda flow_task: TaskStub()))
            def task_func(self, activation):
                activation.prepare()
                FlowStub.method_called = True
                activation.done()
                return activation

        Flow.instance = Flow()
        flow_task = self.init_node(Flow.func_task, flow_cls=Flow, name='task')

        act = flow_task.run()
        self.assertEqual(act.task.status, STATUS.DONE)
        self.assertTrue(FlowStub.method_called)

    def test_handler_activation_lifecycle(self):
        def handler(activation):
            pass

        flow_task = self.init_node(flow.Handler(handler))

        act = func.HandlerActivation()
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

        act = func.HandlerActivation()
        act.initialize(flow_task, TaskStub())

        # by default errors are propogated
        self.assertRaises(ValueError, act.perform)

        # disable gate error propogation
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
            handler_task = flow.Handler()
            method_called = False

            def task_handler(self, activation):
                Flow.method_called = True

        Flow.instance = Flow()
        flow_task = self.init_node(Flow.handler_task, flow_cls=Flow, name='task')

        act = func.HandlerActivation()
        act.initialize(flow_task, TaskStub())

        # execute
        act.perform()
        self.assertEqual(act.task.status, STATUS.DONE)
        self.assertEqual(act.task.status, STATUS.DONE)
        self.assertTrue(Flow.method_called)


class ProcessStub(object):
    _default_manager = mock.Mock()

    def __init__(self, flow_cls=None):
        self.flow_cls = flow_cls

    def active_tasks(self):
        return []

    def save(self):
        return


class TaskStub(object):
    _default_manager = mock.Mock()

    def __init__(self, flow_task=None):
        self.flow_task = flow_task
        self.process_id = 1
        self.pk = 1
        self.status = STATUS.NEW

    @property
    def leading(self):
        from viewflow.models import Task
        return Task.objects.none()

    def save(self):
        return


class FlowStub(object):
    process_cls = ProcessStub
    task_cls = TaskStub
    lock_impl = lock.no_lock
    instance = None


class UserStub(object):
    pass
