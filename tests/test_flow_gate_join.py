from django.test import TestCase

from viewflow import flow
from viewflow.base import this, Flow


class Test(TestCase):
    def test_join_usecase(self):
        act = JoinTestFlow.start.run()
        JoinTestFlow.task1.run(act.process.get_task(JoinTestFlow.task1))
        JoinTestFlow.task2.run(act.process.get_task(JoinTestFlow.task2))

        tasks = act.process.task_set.all()
        self.assertEqual(6, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))

    def test_join_with_canceled_tasks(self):
        act = JoinTestFlow.start.run()
        
        # cancel first task
        task1 = act.process.get_task(JoinTestFlow.task1)
        task1.activate().cancel()

        # execute second
        JoinTestFlow.task2.run(act.process.get_task(JoinTestFlow.task2))

        tasks = act.process.task_set.all()
        self.assertEqual(6, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))


@flow.flow_func
def func(activation, task):
    activation.prepare()
    activation.done()


class JoinTestFlow(Flow):
    start = flow.StartFunction().Next(this.split)
    split = flow.Split().Next(this.task1).Next(this.task2)
    task1 = flow.Function(func, task_loader=lambda flow_task, task: task).Next(this.join)
    task2 = flow.Function(func, task_loader=lambda flow_task, task: task).Next(this.join)
    join = flow.Join().Next(this.end)
    end = flow.End()
