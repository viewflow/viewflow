from django.db import models, transaction
from django.test import TestCase

from viewflow import flow
from viewflow.activation import Context
from viewflow.base import Flow, this
from viewflow.models import Process, Task

from .. import integration_test


def create_test_flow(activation, throw_error=False):
    activation.prepare()
    activation.process.throw_error = throw_error
    activation.done()
    return activation


class BrokenGateProcess(Process):
    throw_error = models.BooleanField(default=False)

    def test(self):
        if self.throw_error:
            raise ValueError('Process raised error')

    class Meta:
        app_label = 'integration'


class BrokenGateFlow(Flow):
    process_cls = BrokenGateProcess

    start = flow.StartFunction(create_test_flow).Next(this.gate)
    gate = flow.If(lambda process: process.test()).OnTrue(this.end).OnFalse(this.end)
    end = flow.End()


@integration_test
class TestBrokenGate(TestCase):
    def test_success_gate_start_succed(self):
        activation = BrokenGateFlow.start.run(throw_error=False)

        process = BrokenGateProcess.objects.get(pk=activation.process.pk)
        self.assertEqual(Process.STATUS.FINISHED, process.status)

    def test_broken_gate_start_failed(self):
        try:
            with transaction.atomic():
                BrokenGateFlow.start.run(throw_error=True)
        except ValueError:
            pass
        else:
            self.fail('No error in gate activation')

        self.assertEqual(0, BrokenGateProcess.objects.count())

    def test_broken_gate_propagate_disabled(self):
        # Start with exception propagation disabled
        activation = None
        with Context(propagate_exception=False):
            activation = BrokenGateFlow.start.run(throw_error=True)

        # Process created, but there is a task in errpr state
        self.assertEqual(1, BrokenGateProcess.objects.count())

        task = activation.process.get_task(BrokenGateFlow.gate, status=Task.STATUS.ERROR)

        # Fix process data and resume task
        process = BrokenGateProcess.objects.get(pk=task.process_id)
        process.throw_error = False
        process.save()

        BrokenGateFlow.gate.resume(task)

        # Great, process, finished successfully
        process = BrokenGateProcess.objects.get(pk=task.process_id)
        self.assertEqual(Process.STATUS.FINISHED, process.status)
