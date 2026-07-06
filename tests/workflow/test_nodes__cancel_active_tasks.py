from django.test import TestCase

from viewflow import this
from viewflow.workflow import flow
from viewflow.workflow.exceptions import FlowRuntimeError
from viewflow.workflow.status import STATUS


class TestJoinCancelWorkflow(flow.Flow):  # noqa: D101
    start = flow.StartHandle().Next(this.split)

    split = flow.Split().Next(this.a).Next(this.b).Next(this.c)

    a = flow.Handle(this.handler).Next(this.join)
    b = flow.Handle(this.handler).Next(this.join)
    c = flow.Handle(this.handler).Next(this.join)

    join = flow.Join(continue_on_condition=this.two_done).Next(this.end)

    end = flow.End()

    def handler(self, activation):
        pass

    def two_done(self, activation, active_tasks):
        return activation.task.previous.filter(status=STATUS.DONE).count() >= 2


class TestJoinCancelError(TestCase):
    def test_uncancellable_active_task_raises_flow_runtime_error(self):
        # cancel_active_tasks's "cannot cancel" guard did
        # ",".join(activation.task for ...) where `task` is a Task model
        # instance, not a string -- str.join() raised TypeError instead
        # of the intended FlowRuntimeError.
        process = TestJoinCancelWorkflow.start.run()
        a = process.task_set.get(flow_task=TestJoinCancelWorkflow.a)
        b = process.task_set.get(flow_task=TestJoinCancelWorkflow.b)
        c = process.task_set.get(flow_task=TestJoinCancelWorkflow.c)

        TestJoinCancelWorkflow.a.run(a)

        # Move c past STATUS.NEW so it can no longer be cancelled
        # (Handle.cancel only allows source=STATUS.NEW) by the time the
        # join's continue_on_condition fires and tries to cancel it.
        c_activation = TestJoinCancelWorkflow.c.activation_class(c)
        c_activation.run(None)
        c_activation.task.save()
        c.refresh_from_db()
        self.assertEqual(c.status, STATUS.STARTED)

        with self.assertRaises(FlowRuntimeError):
            TestJoinCancelWorkflow.b.run(b)


class TestSplitFirstCancelWorkflow(flow.Flow):  # noqa: D101
    start = flow.StartHandle().Next(this.split)

    split = flow.SplitFirst().Next(this.case_1).Next(this.case_2)

    case_1 = flow.Handle(this.handler).Next(this.end)
    case_2 = flow.Handle(this.handler).Next(this.end)

    end = flow.End()

    def handler(self, activation):
        pass


class TestSplitFirstCancelError(TestCase):
    def test_uncancellable_active_task_raises_flow_runtime_error(self):
        process = TestSplitFirstCancelWorkflow.start.run()
        case_1 = process.task_set.get(flow_task=TestSplitFirstCancelWorkflow.case_1)
        case_2 = process.task_set.get(flow_task=TestSplitFirstCancelWorkflow.case_2)

        # Move case_2 past STATUS.NEW so it can no longer be cancelled
        # once case_1 completes first and tries to cancel it.
        case_2_activation = TestSplitFirstCancelWorkflow.case_2.activation_class(case_2)
        case_2_activation.run(None)
        case_2_activation.task.save()
        case_2.refresh_from_db()
        self.assertEqual(case_2.status, STATUS.STARTED)

        with self.assertRaises(FlowRuntimeError):
            TestSplitFirstCancelWorkflow.case_1.run(case_1)
