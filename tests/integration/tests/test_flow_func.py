from django.test import TestCase

from viewflow import flow
from viewflow.base import Flow, this

from .. import integration_test


def create_test_flow(activation):
    activation.prepare()
    activation.done()
    return activation


@flow.flow_func(task_loader=lambda flow_task, process: process.get_task(FunctionFlow.func_task))
def function_task(activation, process):
    activation.prepare()
    activation.done()


def handler(activation):
    pass


class FunctionFlow(Flow):
    start = flow.StartFunction(create_test_flow).Next(this.func_task)
    default_start = flow.StartFunction().Next(this.func_task)
    inline_start = flow.StartFunction().Next(this.func_task)
    func_task = flow.Function(function_task).Next(this.handler_task)
    handler_task = flow.Handler(handler).Next(this.end)
    end = flow.End()

    def inline_start_func(self, activation):
        activation.prepare()
        activation.done()
        self.inline_start_func_called = True
        return activation


@integration_test
class TestFunctionFlow(TestCase):
    def test_function_flow(self):
        act = FunctionFlow.start.run()
        FunctionFlow.func_task.run(act.process)

        tasks = act.process.task_set.all()
        self.assertEqual(4, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))

    def test_function_default_start(self):
        act = FunctionFlow.default_start.run()
        FunctionFlow.func_task.run(act.process)

        tasks = act.process.task_set.all()
        self.assertEqual(4, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))

    def test_function_inline_start(self):
        act = FunctionFlow.inline_start.run()

        self.assertTrue(getattr(FunctionFlow.instance, 'inline_start_func_called', False))
        FunctionFlow.func_task.run(act.process)

        tasks = act.process.task_set.all()
        self.assertEqual(4, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))
