from unittest import mock
from django.test import TestCase

from viewflow import activation, flow
from viewflow.models import Task


class TestActivations(TestCase):
    def test_start_activation_lifecycle(self):
        flow_task_mock = mock.Mock(spec=flow.Start())

        act = activation.StartActivation()
        act.initialize(flow_task_mock)
        act.prepare()
        act.done()

        act.task.prepare.assert_called_once_with()
        act.task.done.assert_called_once_with()
        act.process.start.assert_called_once_with()
        flow_task_mock.activate_next.assert_any_call(act)

    def test_view_activation_activate(self):
        flow_task_mock = mock.Mock(spec=flow.View(lambda *args, **kwargs: None))
        prev_activation_mock = mock.Mock(spec=activation.StartActivation())

        act = activation.ViewActivation.activate(flow_task_mock, prev_activation_mock)

        act.task.save.assert_has_calls(())

    def test_view_activation_lifecycle(self):
        flow_task_mock = mock.Mock(spec=flow.View(lambda *args, **kwargs: None))
        task_mock = mock.Mock(spec=Task())

        act = activation.ViewActivation()
        act.initialize(flow_task_mock, task_mock)
        act.prepare()
        act.done()

        act.task.prepare.assert_called_once_with()
        act.task.done.assert_called_once_with()
        flow_task_mock.activate_next.assert_any_call(act)
