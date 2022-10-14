from django.test import TestCase

from viewflow import this
from viewflow.workflow import flow
from viewflow.workflow.status import STATUS


class Test(TestCase):  # noqa: D101
    def test_join_async(self):
        process = TestASyncWorkflow.start.run()

        first_task = process.task_set.filter(flow_task=TestASyncWorkflow.first).first()
        second_task = process.task_set.filter(flow_task=TestASyncWorkflow.second).first()

        TestASyncWorkflow.first.run(first_task)

        join_task = process.task_set.filter(flow_task=TestASyncWorkflow.join).first()
        self.assertEqual(join_task.status, STATUS.STARTED)

        TestASyncWorkflow.second.run(second_task)
        join_task.refresh_from_db()
        self.assertEqual(join_task.status, STATUS.DONE)

        process.refresh_from_db()
        self.assertEqual(process.status, STATUS.DONE)
        self.assertEqual(process.task_set.count(), 6)

    def test_join_sync(self):
        process = TestSyncWorkflow.start.run()
        process.refresh_from_db()
        self.assertEqual(process.status, STATUS.DONE)
        self.assertEqual(process.task_set.count(), 6)


class TestSyncWorkflow(flow.Flow):  # noqa: D101
    start = flow.StartHandle().Next(this.split)

    split = (
        flow.Split()
        .Next(this.first)
        .Next(this.second)
    )

    first = flow.Function(this.func).Next(this.join)
    second = flow.Function(this.func).Next(this.join)

    join = flow.Join().Next(this.end)

    end = flow.End()

    def func(self, activation):
        pass


class TestASyncWorkflow(flow.Flow):  # noqa: D101
    start = flow.StartHandle().Next(this.split)

    split = (
        flow.Split()
        .Next(this.first)
        .Next(this.second)
    )

    first = flow.Handle(this.handler).Next(this.join)
    second = flow.Handle(this.handler).Next(this.join)

    join = flow.Join().Next(this.end)

    end = flow.End()

    def handler(self, activation):
        pass
