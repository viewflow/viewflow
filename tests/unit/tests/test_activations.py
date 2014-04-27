from unittest import mock
from django.test import TestCase

from viewflow import activation, flow
from viewflow.flow import gates
from viewflow.models import Process, Task
from viewflow.token import Token


class TestStartActivation(TestCase):
    def test_start_activation_lifecycle(self):
        flow_task_mock = mock.Mock(spec=flow.Start())
        flow_task_mock._outgoing = mock.Mock(return_value=[])

        act = activation.StartActivation()
        act.initialize(flow_task_mock)
        act.prepare()
        act.done()

        act.task.prepare.assert_called_once_with()
        act.task.done.assert_called_once_with()
        act.process.start.assert_called_once_with()
        flow_task_mock._outgoing.assert_any_call()


class TestViewActivation(TestCase):
    def test_view_activation_activate(self):
        flow_task_mock = mock.Mock(spec=flow.View(lambda *args, **kwargs: None))
        flow_task_mock._outgoing = mock.Mock(return_value=[])
        prev_activation_mock = mock.Mock(spec=activation.StartActivation())

        act = activation.ViewActivation.activate(flow_task_mock, prev_activation_mock, Token('start'))

        act.task.save.assert_has_calls(())

    def test_view_activation_lifecycle(self):
        flow_task_mock = mock.Mock(spec=flow.View(lambda *args, **kwargs: None))
        flow_task_mock._outgoing = mock.Mock(return_value=[])
        task_mock = mock.Mock(spec=Task())

        act = activation.ViewActivation()
        act.initialize(flow_task_mock, task_mock)
        act.prepare()
        act.done()

        act.task.prepare.assert_called_once_with()
        act.task.done.assert_called_once_with()
        flow_task_mock._outgoing.assert_any_call()


class TestJobActivation(TestCase):
    def test_job_activation_activate(self):
        flow_task_mock = mock.Mock(spec=flow.Job(lambda *args, **kwargs: None))
        flow_task_mock._outgoing = mock.Mock(return_value=[])
        prev_activation_mock = mock.Mock(spec=activation.StartActivation())

        with mock.patch('viewflow.activation.get_task_ref'):
            act = activation.JobActivation.activate(flow_task_mock, prev_activation_mock, Token('start'))
            act.task.save.assert_has_calls(())
            self.assertEquals(1, flow_task_mock.job.apply_async.call_count)

    def test_job_activation_lifecycle(self):
        flow_task_mock = mock.Mock(spec=flow.Job(lambda *args, **kwargs: None))
        flow_task_mock._outgoing = mock.Mock(return_value=[])
        task_mock = mock.Mock(spec=Task())

        act = activation.JobActivation()
        act.initialize(flow_task_mock, task_mock)
        act.prepare()
        act.start()
        act.done(result=None)

        act.task.done.assert_called_once_with()
        flow_task_mock._outgoing.assert_any_call()


class TestEndActivation(TestCase):
    def test_end_activation_activate(self):
        active_task_mock = mock.Mock()
        process_mock = mock.Mock(spec=Process())
        process_mock.active_tasks = mock.Mock(return_value=[active_task_mock])

        flow_task_mock = mock.Mock(spec=flow.End())
        flow_task_mock._outgoing = mock.Mock(return_value=[])
        flow_task_mock.flow_cls.process_cls._default_manager.get = mock.Mock(return_value=process_mock)
        prev_activation_mock = mock.Mock(spec=activation.StartActivation())

        act = activation.EndActivation.activate(flow_task_mock, prev_activation_mock, Token('start'))

        act.task.save.assert_has_calls(())
        act.process.finish.assert_has_calls(())
        active_task_mock.flow_task.deactivate.assert_called_once_with(mock.ANY)


class TestIfActivation(TestCase):
    def test_if_activation_activate(self):
        flow_task_mock = mock.Mock(spec=flow.If(lambda act: True))
        flow_task_mock._outgoing = mock.Mock(return_value=[])
        prev_activation_mock = mock.Mock(spec=activation.StartActivation())

        act = gates.IfActivation.activate(flow_task_mock, prev_activation_mock, Token('start'))
        act.task.save.assert_has_calls(())


class TestSwitchActivation(TestCase):
    def test_switch_activation_activate(self):
        flow_task_mock = mock.Mock(spec=flow.Switch())
        flow_task_mock._outgoing = mock.Mock(return_value=[])
        type(flow_task_mock).branches = mock.PropertyMock(return_value=[(mock.Mock(), lambda p: True)])
        prev_activation_mock = mock.Mock(spec=activation.StartActivation())

        act = gates.SwitchActivation.activate(flow_task_mock, prev_activation_mock, Token('start'))
        act.task.save.assert_has_calls(())


class TestJoinActivation(TestCase):
    def test_join_activation_activate(self):
        prev_task_mock = mock.Mock(spec=Task())
        prev_task_mock.token = Token('start/1_2')

        task_mock = mock.Mock(spec=Task())
        task_mock.previous.all = mock.Mock(return_value=[prev_task_mock])

        flow_task_mock = mock.Mock(spec=flow.Join())
        flow_task_mock._outgoing = mock.Mock(return_value=[])
        flow_task_mock.flow_cls.task_cls = mock.Mock(return_value=task_mock)
        flow_task_mock.flow_cls.task_cls._default_manager.filter = mock.Mock(return_value=Task.objects.none())

        prev_activation_mock = mock.Mock(spec=activation.StartActivation())

        act = gates.JoinActivation.activate(flow_task_mock, prev_activation_mock, Token('start'))
        act.task.save.assert_has_calls(())
        flow_task_mock._outgoing.assert_any_call()


class TestSplitActivation(TestCase):
    def test_switch_activation_activate(self):
        flow_task_mock = mock.Mock(spec=flow.Split())
        flow_task_mock._outgoing = mock.Mock(return_value=[])
        type(flow_task_mock).branches = mock.PropertyMock(return_value=[(mock.Mock(), lambda p: True)])
        prev_activation_mock = mock.Mock(spec=activation.StartActivation())

        act = gates.SplitActivation.activate(flow_task_mock, prev_activation_mock, Token('start'))
        act.task.save.assert_has_calls(())
