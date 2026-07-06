from django.test import TestCase

from viewflow import this
from viewflow.workflow import flow
from viewflow.workflow.context import Context
from viewflow.workflow.signals import task_finished
from viewflow.workflow.status import STATUS


class JoinCompleteError(Exception):
    """Raised by a task_finished receiver to fail a join while it completes."""


def _raise_on_join_finish(sender, process, task, **kwargs):
    if task.flow_task.name == "join":
        raise JoinCompleteError("boom in join complete")


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


class TestJoinErrorHandling(TestCase):
    """A join that errors while completing follows the activation context:
    a background trigger records ERROR (recoverable); a user trigger propagates."""

    def setUp(self):
        task_finished.connect(_raise_on_join_finish)
        self.addCleanup(task_finished.disconnect, _raise_on_join_finish)

    def _run_first_branch(self):
        process = TestJoinErrorWorkflow.start.run()
        first = process.task_set.get(flow_task=TestJoinErrorWorkflow.first)
        second = process.task_set.get(flow_task=TestJoinErrorWorkflow.second)
        TestJoinErrorWorkflow.first.run(first)  # join created, STARTED
        return process, second

    def test_background_trigger_marks_join_error_and_keeps_process(self):
        process, second = self._run_first_branch()

        # Completing the last branch triggers the join. propagate_exception=False
        # mirrors a Job node's activate_next(): the error is recorded, not raised.
        with Context(propagate_exception=False):
            TestJoinErrorWorkflow.second.run(second)

        join_task = process.task_set.get(flow_task=TestJoinErrorWorkflow.join)
        self.assertEqual(join_task.status, STATUS.ERROR)

        second.refresh_from_db()
        self.assertEqual(second.status, STATUS.DONE)

        process.refresh_from_db()
        self.assertNotEqual(process.status, STATUS.DONE)
        # the errored join must not have created its next task
        self.assertFalse(
            process.task_set.filter(flow_task=TestJoinErrorWorkflow.end).exists()
        )

    def test_user_trigger_propagates_join_error(self):
        process, second = self._run_first_branch()

        # Default context (propagate_exception=True): the error reaches the
        # caller that triggered the join instead of being swallowed.
        with self.assertRaises(JoinCompleteError):
            TestJoinErrorWorkflow.second.run(second)


class TestJoinErrorWorkflow(flow.Flow):  # noqa: D101
    start = flow.StartHandle().Next(this.split)

    split = flow.Split().Next(this.first).Next(this.second)

    first = flow.Handle(this.handler).Next(this.join)
    second = flow.Handle(this.handler).Next(this.join)

    join = flow.Join().Next(this.end)

    end = flow.End()

    def handler(self, activation):
        pass


class TestPartialJoin(TestCase):
    """continue_on_condition still fires and cancels active branches after the
    is_done/complete split."""

    def test_partial_join_continues_after_two_of_three(self):
        process = TestPartialJoinWorkflow.start.run()
        a = process.task_set.get(flow_task=TestPartialJoinWorkflow.a)
        b = process.task_set.get(flow_task=TestPartialJoinWorkflow.b)
        c = process.task_set.get(flow_task=TestPartialJoinWorkflow.c)

        TestPartialJoinWorkflow.a.run(a)
        join_task = process.task_set.get(flow_task=TestPartialJoinWorkflow.join)
        self.assertEqual(join_task.status, STATUS.STARTED)  # only one branch done

        TestPartialJoinWorkflow.b.run(b)  # two done -> continue_on_condition fires

        join_task.refresh_from_db()
        self.assertEqual(join_task.status, STATUS.DONE)

        c.refresh_from_db()
        self.assertEqual(c.status, STATUS.CANCELED)

        process.refresh_from_db()
        self.assertEqual(process.status, STATUS.DONE)


class TestPartialJoinWorkflow(flow.Flow):  # noqa: D101
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
