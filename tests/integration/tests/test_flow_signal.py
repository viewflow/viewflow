from django.dispatch import Signal
from django.test import TestCase

from viewflow import flow
from viewflow.base import Flow, this

from .. import integration_test


test_start_signal = Signal()
test_task_signal = Signal(providing_args=["process"])


def create_test_flow(activation, **kwargs):
    activation.prepare()
    activation.done()
    return activation


@flow.flow_signal(task_loader=lambda flow_task, **kwargs: kwargs['process'].get_task(SignalFlow.signal_task))
def signal_task(activation, **kwargs):
    activation.prepare()
    activation.done()


def handler(activation):
    pass


class SignalFlow(Flow):
    start = flow.StartSignal(test_start_signal, create_test_flow).Next(this.signal_task)
    signal_task = flow.Signal(test_task_signal, signal_task).Next(this.end)
    end = flow.End()


@integration_test
class TestFunctionFlow(TestCase):
    def test_function_flow(self):
        test_start_signal.send(sender=self)
        process = SignalFlow.process_cls.objects.get()
        test_task_signal.send(sender=self, process=process)

        tasks = process.task_set.all()
        self.assertEqual(3, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))
