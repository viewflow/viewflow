from django.test import TestCase
from viewflow import this
from viewflow.workflow import flow, PROCESS, STATUS


class Test(TestCase):
    def test_undo_start(self):
        # forward flow
        process = TestUndoFlow.start.run()

        # cancel uncompleted handle
        handle_task = process.task_set.get(flow_task=TestUndoFlow.handle)
        with handle_task.activation() as activation:
            activation.cancel()

        # undo flow start
        start_task = process.task_set.get(flow_task=TestUndoFlow.start)
        with start_task.activation() as activation:
            activation.undo()

        process.refresh_from_db()
        self.assertTrue(process.finished)
        self.assertEqual(PROCESS.CANCELED, process.status)

    def test_undo_completed_handle(self):
        # forward flow
        process = TestUndoFlow.start.run()
        TestUndoFlow.handle.run(
            task=process.task_set.get(flow_task=TestUndoFlow.handle)
        )
        process.refresh_from_db()
        self.assertTrue(process.finished)

        # undo process finale
        end_task = process.task_set.get(flow_task=TestUndoFlow.end)
        with end_task.activation() as activation:
            activation.undo()

        # undo handle
        handle_task = process.task_set.get(flow_task=TestUndoFlow.handle)
        with handle_task.activation() as activation:
            activation.undo()

        handle_task.refresh_from_db()
        self.assertEqual(STATUS.CANCELED, handle_task.status)

        # recreate and rerun handle
        with handle_task.activation() as activation:
            activation.revive()
        TestUndoFlow.handle.run(
            task=process.task_set.get(flow_task=TestUndoFlow.handle, status=STATUS.NEW)
        )
        process.refresh_from_db()
        self.assertTrue(process.finished)
        self.assertEqual(
            2, process.task_set.filter(flow_task=TestUndoFlow.handle).count()
        )

    def test_undo_end(self):
        # forward flow
        process = TestUndoFlow.start.run()
        TestUndoFlow.handle.run(
            task=process.task_set.get(flow_task=TestUndoFlow.handle)
        )
        process.refresh_from_db()
        self.assertTrue(process.finished)

        # undo process finale
        end_task = process.task_set.get(flow_task=TestUndoFlow.end)
        with end_task.activation() as activation:
            activation.undo()

        process.refresh_from_db()
        self.assertFalse(process.finished)
        self.assertEqual(PROCESS.NEW, process.status)

        # redo process finale
        end_task = process.task_set.get(flow_task=TestUndoFlow.end)
        with end_task.activation() as activation:
            activation.revive()

        process.refresh_from_db()
        self.assertTrue(process.finished)
        self.assertEqual(PROCESS.DONE, process.status)

        self.assertEqual(2, process.task_set.filter(flow_task=TestUndoFlow.end).count())


class TestUndoFlow(flow.Flow):
    start = flow.StartHandle().Next(this.handle)
    handle = flow.Handle().Next(this.end)
    end = flow.End()
