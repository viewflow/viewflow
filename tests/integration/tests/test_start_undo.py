from django.test import TestCase

from viewflow import flow
from viewflow.activation import STATUS
from viewflow.base import Flow, this

from .. import integration_test


def create_test_flow(activation):
    activation.prepare()
    activation.done()
    return activation


@flow.flow_func(task_loader=lambda flow_task, process: process.get_task(StartUndoFlow.func_task))
def function_task(activation, process):
    activation.prepare()
    activation.done()


class StartUndoFlow(Flow):
    start = flow.StartFunction(create_test_flow).Next(this.func_task)
    func_task = flow.Function(function_task).Next(this.end)
    end = flow.End()

    def start_undo(self, activation):
        self.handler_called = True


@integration_test
class TestStartUndoFlow(TestCase):
    def test_start_undo_cancels_process(self):
        act = StartUndoFlow.start.run()

        # Undo
        func_task = act.process.get_task(StartUndoFlow.func_task, status=STATUS.NEW)
        func_task.activate().cancel()

        start_task = act.process.get_task(StartUndoFlow.start, status=STATUS.DONE)
        start_act = start_task.activate()
        start_act.undo()
        self.assertTrue(getattr(StartUndoFlow.instance, 'handler_called', False))

        process = StartUndoFlow.process_cls.objects.get(pk=start_act.process.pk)
        self.assertEqual(STATUS.CANCELED, process.status)
