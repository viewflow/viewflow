from django.test import TestCase

from viewflow import flow
from viewflow.activation import STATUS
from viewflow.base import Flow, this


# flow.Switch

def create_test_flow(activation):
    activation.prepare()
    activation.done()
    return activation


@flow.flow_func(task_loader=lambda flow_task, task: task)
def function_task(activation, task):
    activation.prepare()
    activation.done()


def handler(activation):
    pass


class IfTestFlow(Flow):
    start = flow.StartFunction(create_test_flow).Next(this.if_task)
    if_task = flow.If(cond=lambda process: True).OnTrue(this.on_true).OnFalse(this.on_false)
    on_true = flow.Handler(handler).Next(this.end)
    on_false = flow.Handler(handler).Next(this.end)
    end = flow.End()


class SplitJoinTestFlow(Flow):
    start = flow.StartFunction(create_test_flow).Next(this.split)
    split = flow.Split().Next(this.task1).Next(this.task2).Next(this.task3, cond=lambda process: False)
    task1 = flow.Function(function_task).Next(this.join)
    task2 = flow.Function(function_task).Next(this.join)
    task3 = flow.Function(function_task).Next(this.join)
    join = flow.Join().Next(this.end)
    end = flow.End()


class SwitchTestFlow(Flow):
    start = flow.StartFunction(create_test_flow).Next(this.switch)
    switch = flow.Switch().Case(this.task1, cond=lambda process: True).Default(this.task2)
    task1 = flow.Handler(handler).Next(this.end)
    task2 = flow.Handler(handler).Next(this.end)
    end = flow.End()


class TestGates(TestCase):
    def test_if_flow_succeed(self):
        IfTestFlow.start.run()

        process = IfTestFlow.process_cls.objects.get()
        tasks = process.task_set.all()

        self.assertEqual(4, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))

        process.get_task(IfTestFlow.on_true, status=STATUS.DONE)

    def test_split_join_flow_succeed(self):
        SplitJoinTestFlow.start.run()

        process = SplitJoinTestFlow.process_cls.objects.get()
        SplitJoinTestFlow.task1.run(process.get_task(SplitJoinTestFlow.task1))
        SplitJoinTestFlow.task2.run(process.get_task(SplitJoinTestFlow.task2))
        tasks = process.task_set.all()

        self.assertEqual(6, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))

    def test_switch_flow_succeed(self):
        SwitchTestFlow.start.run()

        process = SwitchTestFlow.process_cls.objects.get()
        tasks = process.task_set.all()

        self.assertEqual(4, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))
