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
    func_task = flow.Function(function_task).Next(this.handler_task)
    handler_task = flow.Handler(handler).Next(this.end)
    end = flow.End()


@integration_test
class TestFunctionFlow(TestCase):
    def test_function_flow(self):
        act = FunctionFlow.start.run()
        FunctionFlow.func_task.run(act.process)

        tasks = act.process.task_set.all()
        self.assertEqual(4, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))
