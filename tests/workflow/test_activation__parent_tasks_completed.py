from types import SimpleNamespace

from django.test import TestCase

from viewflow import this
from viewflow.workflow import flow, STATUS
from viewflow.workflow.activation import parent_tasks_completed


def _noop(activation):
    pass


class TestFlow(flow.Flow):
    start = flow.StartHandle().Next(this.func1)
    func1 = flow.Function(_noop).Next(this.func2)
    func2 = flow.Function(_noop).Next(this.end)
    end = flow.End()


class Test(TestCase):
    # all() takes exactly one iterable, so all(lambda task: ..., previous)
    # raised TypeError -- the predicate was never evaluated, and `previous`
    # (a .values("status") queryset of dicts) wouldn't support `task.status`
    # attribute access even if called correctly. Currently unused, so this
    # only surfaces via a direct unit test.
    def test_returns_true_when_every_previous_task_is_done(self):
        TestFlow.start.run()
        func2_task = TestFlow.task_class.objects.get(flow_task=TestFlow.func2)

        self.assertTrue(
            parent_tasks_completed(SimpleNamespace(task=func2_task))
        )

    def test_returns_false_when_a_previous_task_is_not_done(self):
        TestFlow.start.run()
        func2_task = TestFlow.task_class.objects.get(flow_task=TestFlow.func2)
        func1_task = func2_task.previous.get()
        func1_task.status = STATUS.NEW
        func1_task.save()

        self.assertFalse(
            parent_tasks_completed(SimpleNamespace(task=func2_task))
        )
