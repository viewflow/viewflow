from django.test import TestCase

from viewflow import this
from viewflow.workflow import flow
from viewflow.workflow.status import STATUS


class TestJoinWorkflow(flow.Flow):  # noqa: D101
    start = flow.StartHandle().Next(this.split)

    split = flow.Split().Next(this.a).Next(this.b)

    a = flow.Handle(this.handler).Next(this.join)
    b = flow.Handle(this.handler).Next(this.join)

    join = flow.Join(continue_on_condition=this.two_done).Next(this.end)

    end = flow.End()

    def handler(self, activation):
        pass

    def two_done(self, activation, active_tasks):
        # Never actually true with only 2 branches and 1 done -- keeps
        # the join waiting after `a` completes, so the test can drive
        # complete() manually.
        return activation.task.previous.filter(status=STATUS.DONE).count() >= 2


class Test(TestCase):
    def test_complete_does_not_crash_when_every_previous_task_is_canceled(self):
        # complete() only guarded len(join_prefixes) > 1 (an ambiguous
        # multi-token state); it never guarded the empty case.
        # _join_token_prefixes() excludes CANCELED/REVIVED previous
        # tasks, so if every incoming task ends up cancelled (e.g. all
        # were undone) before the join completes, join_prefixes is an
        # empty set and next(iter(join_prefixes)) raised StopIteration
        # instead of being handled gracefully.
        process = TestJoinWorkflow.start.run()
        a = process.task_set.get(flow_task=TestJoinWorkflow.a)

        TestJoinWorkflow.a.run(a)  # creates the join task, linked to `a` via previous

        join_task = process.task_set.get(flow_task=TestJoinWorkflow.join)
        self.assertEqual(join_task.status, STATUS.STARTED)

        # Simulate `a` having since been cancelled/undone.
        a.refresh_from_db()
        a.status = STATUS.CANCELED
        a.save()

        # complete()'s own transition condition is is_done(), which
        # already correctly returns False for an empty prefix set --
        # so the buggy body is only reachable if that check and the
        # transition's own re-check race with a concurrent status
        # change. .original() bypasses the FSM condition gate to
        # exercise the body directly, the same way that race would.
        join_activation = TestJoinWorkflow.join.activation_class(join_task)
        join_activation.complete.original()  # must not raise StopIteration

        join_task.refresh_from_db()
        self.assertIsNotNone(join_task.finished)
