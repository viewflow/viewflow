from django.test import TestCase

from viewflow import flow
from viewflow.activation import STATUS
from viewflow.base import Flow, this

from .. import integration_test


def create_test_flow(activation):
    activation.prepare()
    activation.done()
    return activation


def handler(activation):
    pass


class EndUndoFlow(Flow):
    start = flow.StartFunction(create_test_flow).Next(this.func_task)
    func_task = flow.Handler(handler).Next(this.end)
    end = flow.End()


@integration_test
class TestEndUndoFlow(TestCase):
    def test_end_undo_reactivates_process(self):
        act = EndUndoFlow.start.run()
        process = EndUndoFlow.process_cls.objects.get(pk=act.process.pk)
        self.assertEqual(STATUS.DONE, process.status)

        # Undo
        end_task = act.process.get_task(EndUndoFlow.end, status=STATUS.DONE)
        end_act = end_task.activate()
        end_act.undo()
        end_act.cancel()

        process = EndUndoFlow.process_cls.objects.get(pk=act.process.pk)
        self.assertEqual(STATUS.NEW, process.status)

        # Reactivate
        func_task = act.process.get_task(EndUndoFlow.func_task, status=STATUS.DONE)
        func_task.activate().activate_next()

        act.process.get_task(EndUndoFlow.end, status=STATUS.DONE)
        process = EndUndoFlow.process_cls.objects.get(pk=act.process.pk)
        self.assertEqual(STATUS.DONE, process.status)
