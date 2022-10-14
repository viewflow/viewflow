from django.test import TestCase

from viewflow import this
from viewflow.workflow import flow, PROCESS, STATUS


class Test(TestCase):
    def test_undo_gates(self):
        # forward flow
        process = TestUndoFlow.start.run()
        TestUndoFlow.handle_a.run(
            task=process.task_set.get(flow_task=TestUndoFlow.handle_a)
        )
        TestUndoFlow.handle_d.run(
            task=process.task_set.get(flow_task=TestUndoFlow.handle_d)
        )

        # undo process finale
        end_task = process.task_set.get(flow_task=TestUndoFlow.end)
        with end_task.activation() as activation:
            activation.undo()

        # undo join
        join_task = process.task_set.get(flow_task=TestUndoFlow.join_gate)
        with join_task.activation() as activation:
            activation.undo()

        # undo handle_d
        handle_d_task = process.task_set.get(flow_task=TestUndoFlow.handle_d)
        with handle_d_task.activation() as activation:
            activation.undo()

        # undo switch
        switch_task = process.task_set.get(flow_task=TestUndoFlow.switch_gate)
        with switch_task.activation() as activation:
            activation.undo()

        # undo handle_a
        handle_a_task = process.task_set.get(flow_task=TestUndoFlow.handle_a)
        with handle_a_task.activation() as activation:
            activation.undo()

        # undo if gate
        if_task = process.task_set.get(flow_task=TestUndoFlow.if_gate)
        with if_task.activation() as activation:
            activation.undo()

        # undo split gate
        split_task = process.task_set.get(flow_task=TestUndoFlow.split_gate)
        with split_task.activation() as activation:
            activation.undo()

        # undo flow start
        start_task = process.task_set.get(flow_task=TestUndoFlow.start)
        with start_task.activation() as activation:
            activation.undo()

        process.refresh_from_db()
        self.assertTrue(process.finished)
        self.assertEqual(PROCESS.CANCELED, process.status)

    def test_revive_join(self):
        # forward flow
        process = TestUndoFlow.start.run()
        TestUndoFlow.handle_a.run(
            task=process.task_set.get(flow_task=TestUndoFlow.handle_a)
        )

        # undo join
        join_task = process.task_set.get(flow_task=TestUndoFlow.join_gate)
        with join_task.activation() as activation:
            activation.cancel()

        # run handle_d
        TestUndoFlow.handle_d.run(
            task=process.task_set.get(flow_task=TestUndoFlow.handle_d)
        )

        # undo end/join again
        end_task = process.task_set.get(flow_task=TestUndoFlow.end)
        with end_task.activation() as activation:
            activation.undo()

        join_task = process.task_set.get(flow_task=TestUndoFlow.join_gate, status=STATUS.DONE)
        with join_task.activation() as activation:
            activation.undo()

        # revive join
        with join_task.activation() as activation:
            activation.revive()
        process.refresh_from_db()
        self.assertTrue(process.finished)


    def test_revive_split(self):
        # forward flow
        process = TestUndoFlow.start.run()

        # cancel handles
        handle_a_task = process.task_set.get(flow_task=TestUndoFlow.handle_a)
        with handle_a_task.activation() as activation:
            activation.cancel()
        handle_d_task = process.task_set.get(flow_task=TestUndoFlow.handle_d)
        with handle_d_task.activation() as activation:
            activation.cancel()

        # undo if gate
        if_task = process.task_set.get(flow_task=TestUndoFlow.if_gate)
        with if_task.activation() as activation:
            activation.undo()

        # undo switch
        switch_task = process.task_set.get(flow_task=TestUndoFlow.switch_gate)
        with switch_task.activation() as activation:
            activation.undo()

        # undo split gate
        split_task = process.task_set.get(flow_task=TestUndoFlow.split_gate)
        with split_task.activation() as activation:
            activation.undo()

        # revive split gate
        with split_task.activation() as activation:
            activation.revive()

        TestUndoFlow.handle_a.run(
            task=process.task_set.get(flow_task=TestUndoFlow.handle_a, status=STATUS.NEW),
        )
        TestUndoFlow.handle_d.run(
            task=process.task_set.get(flow_task=TestUndoFlow.handle_d, status=STATUS.NEW)
        )
        process.refresh_from_db()
        self.assertTrue(process.finished)

    def test_revive_if(self):
        # forward flow
        process = TestUndoFlow.start.run()

        # cancel handle_a
        handle_a_task = process.task_set.get(flow_task=TestUndoFlow.handle_a)
        with handle_a_task.activation() as activation:
            activation.cancel()

        # undo if gate
        if_task = process.task_set.get(flow_task=TestUndoFlow.if_gate)
        with if_task.activation() as activation:
            activation.undo()

        # revive if gate
        with if_task.activation() as activation:
            activation.revive()

        # complete process as usual
        TestUndoFlow.handle_a.run(
            task=process.task_set.get(flow_task=TestUndoFlow.handle_a, status=STATUS.NEW),
        )
        TestUndoFlow.handle_d.run(
            task=process.task_set.get(flow_task=TestUndoFlow.handle_d, status=STATUS.NEW)
        )
        process.refresh_from_db()
        self.assertTrue(process.finished)


class TestUndoFlow(flow.Flow):
    start = flow.StartHandle().Next(this.split_gate)
    split_gate = flow.Split().Next(this.if_gate).Next(this.switch_gate)

    if_gate = flow.If(lambda act: True).Then(this.handle_a).Else(this.handle_b)
    handle_a = flow.Handle().Next(this.join_gate)
    handle_b = flow.Handle().Next(this.join_gate)

    switch_gate = (
        flow.Switch()
        .Case(this.handle_c, lambda act: False)
        .Case(this.handle_d, lambda act: True)
    )
    handle_c = flow.Handle().Next(this.join_gate)
    handle_d = flow.Handle().Next(this.join_gate)

    join_gate = flow.Join().Next(this.end)

    end = flow.End()
