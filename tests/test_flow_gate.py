try:
    from unittest import mock
except ImportError:
    import mock

from django.test import TestCase

from viewflow import lock
from viewflow.activation import STATUS
from viewflow.flow import If, Switch
from viewflow.nodes.ifgate import IfActivation
from viewflow.nodes.switch import SwitchActivation


class Test(TestCase):
    def init_node(self, node, flow_class=None, name='test_node'):
        node.flow_class = flow_class or FlowStub
        node.name = name
        return node

    def setUp(self):
        ProcessStub._default_manager.get.return_value = ProcessStub()
        TaskStub._default_manager.get.return_value = TaskStub()
        FlowStub.instance = FlowStub()
        FlowTaskStub.activated = False

    def test_if_activation_activate_true(self):
        next_task = FlowTaskStub()
        flow_task = self.init_node(If(lambda process: True).Then(next_task))

        act = IfActivation()
        act.initialize(flow_task, TaskStub())
        act.perform()

        self.assertTrue(FlowTaskStub.activated)

    def test_if_activation_activate_false(self):
        next_task = FlowTaskStub()
        flow_task = self.init_node(If(lambda process: False).Else(next_task))

        act = IfActivation()
        act.initialize(flow_task, TaskStub())
        act.perform()

        self.assertTrue(FlowTaskStub.activated)

    def test_switch_activation_case(self):
        next_task = FlowTaskStub()
        flow_task = self.init_node(Switch().Case(next_task, cond=lambda process: True))

        act = SwitchActivation()
        act.initialize(flow_task, TaskStub())
        act.perform()

        self.assertTrue(FlowTaskStub.activated)

    def test_switch_activation_default(self):
        next_task = FlowTaskStub()
        flow_task = self.init_node(Switch().Default(next_task))

        act = SwitchActivation()
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

    def __init__(self, flow_class=None):
        self.flow_class = flow_class

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
        self.started = None

    @property
    def leading(self):
        from viewflow.models import Task
        return Task.objects.none()

    def save(self):
        return


class FlowStub(object):
    process_class = ProcessStub
    task_class = TaskStub
    lock_impl = lock.no_lock
    instance = None


class FlowTaskStub(object):
    activated = False

    @classmethod
    def activate(cls, prev_activation, token):
        FlowTaskStub.activated = True
