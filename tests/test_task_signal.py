from contextlib import contextmanager

import mock
from django.test import TestCase
from mock import ANY
from viewflow import flow
from viewflow.base import Flow, this
from viewflow.signals import task_new


@contextmanager
def catch_signal(signal):
    """Catch django signal and return the mocked call.
    https://medium.freecodecamp.org/how-to-testing-django-signals-like-a-pro-c7ed74279311
    """
    handler = mock.Mock()
    signal.connect(handler)
    yield handler
    signal.disconnect(handler)


class FlowView(Flow):
    start = flow.StartFunction().Next(this.task)
    task = flow.View(lambda request: None).Next(this.end)
    end = flow.End()


class TestFlowView(TestCase):
    def test(self):
        with catch_signal(task_new) as handler:
            act = FlowView.start.run()
        task = act.process.get_task(FlowView.task)
        handler.assert_called_once_with(sender=task.process, signal=ANY, task=task)


class FlowSplit(Flow):
    start = flow.StartFunction().Next(this.split)
    split = flow.Split().Next(this.view).Next(this.end)
    view = flow.View(lambda request: None).Next(this.end)
    end = flow.End()


class TestFlowSplit(TestCase):
    def test(self):
        with catch_signal(task_new) as handler:
            act = FlowSplit.start.run()
        task = act.process.get_task(FlowSplit.view)
        handler.assert_called_once_with(sender=task.process, signal=ANY, task=task)


class FlowIf(Flow):
    start = flow.StartFunction().Next(this.iff)
    iff = flow.If(lambda arg: False).Then(this.view).Else(this.view)
    view = flow.View(lambda request: None).Next(this.end)
    end = flow.End()


class TestFlowIf(TestCase):
    def test(self):
        with catch_signal(task_new) as handler:
            act = FlowIf.start.run()
        task = act.process.get_task(FlowIf.view)
        handler.assert_called_once_with(sender=task.process, signal=ANY, task=task)


@flow.flow_func
def func(activation, task):
    activation.prepare()
    activation.done()


class FlowJoin(Flow):
    start = flow.StartFunction().Next(this.split)
    split = flow.Split().Next(this.task1).Next(this.task2)
    task1 = flow.Function(func, task_loader=lambda flow_task, task: task).Next(this.join)
    task2 = flow.Function(func, task_loader=lambda flow_task, task: task).Next(this.join)
    join = flow.Join().Next(this.task3)
    task3 = flow.Function(func, task_loader=lambda flow_task, task: task).Next(this.end)
    end = flow.End()


class TestFlowJoin(TestCase):
    def test(self):
        """Ensures that task_new is called three times.
        """
        with catch_signal(task_new) as handler:
            act = FlowJoin.start.run()
            FlowJoin.task1.run(act.process.get_task(FlowJoin.task1))
            FlowJoin.task2.run(act.process.get_task(FlowJoin.task2))
        arg0, arg1, arg2 = handler.call_args_list
        # TODO test individual that this works
