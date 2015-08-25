from django.test import TestCase

from viewflow import lock
from viewflow.compat import mock
from viewflow.activation import STATUS
from viewflow.flow import gates


class Test(TestCase):
    def init_node(self, node, flow_cls=None, name='test_node'):
        node.flow_cls = flow_cls or FlowStub
        node.name = name
        return node

    def setUp(self):
        ProcessStub._default_manager.get.return_value = ProcessStub()
        TaskStub._default_manager.get.return_value = TaskStub()
        FlowStub.instance = FlowStub()
        FlowTaskStub.activated = False

    def test_if_activation_activate_true(self):
        next_task = FlowTaskStub()
        flow_task = self.init_node(gates.If(lambda process: True).OnTrue(next_task))

        act = gates.IfActivation()
        act.initialize(flow_task, TaskStub())
        act.perform()

        self.assertTrue(FlowTaskStub.activated)

    def test_if_activation_activate_false(self):
        next_task = FlowTaskStub()
        flow_task = self.init_node(gates.If(lambda process: False).OnFalse(next_task))

        act = gates.IfActivation()
        act.initialize(flow_task, TaskStub())
        act.perform()

        self.assertTrue(FlowTaskStub.activated)

    def test_switch_activation_case(self):
        next_task = FlowTaskStub()
        flow_task = self.init_node(gates.Switch().Case(next_task, cond=lambda process: True))

        act = gates.SwitchActivation()
        act.initialize(flow_task, TaskStub())
        act.perform()

        self.assertTrue(FlowTaskStub.activated)

    def test_switch_activation_default(self):
        next_task = FlowTaskStub()
        flow_task = self.init_node(gates.Switch().Default(next_task))

        act = gates.SwitchActivation()
        act.initialize(flow_task, TaskStub())
        act.perform()

        self.assertTrue(FlowTaskStub.activated)

        # undo
        act.undo()
        self.assertEqual(act.task.status, STATUS.NEW)
        act.cancel()
        self.assertEqual(act.task.status, STATUS.CANCELED)


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

    def __init__(self, flow_task=None, token='start/1_2'):
        self.flow_task = flow_task
        self.process_id = 1
        self.pk = 1
        self.status = STATUS.NEW
        self.token = token

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


class FlowTaskStub(object):
    activated = False

    @classmethod
    def activate(cls, prev_activation, token):
        FlowTaskStub.activated = True
