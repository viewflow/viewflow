from django.dispatch import Signal
from django.test import TestCase

from viewflow import flow
from viewflow.base import Flow, this


class Test(TestCase):
    def test_signal_usecase(self):
        start_test_signal.send(sender=self)
        process = SignalFlow.process_cls.objects.get()
        task_test_signal.send(sender=self, process=process)

        tasks = process.task_set.all()
        self.assertEqual(3, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))


start_test_signal = Signal()
task_test_signal = Signal(providing_args=["process"])


def create_flow(activation, **kwargs):
    activation.prepare()
    activation.done()
    return activation


@flow.flow_signal(task_loader=lambda flow_task, **kwargs: kwargs['process'].get_task(SignalFlow.signal_task))
def signal_task(activation, **kwargs):
    activation.prepare()
    activation.done()


class SignalFlow(Flow):
    start = flow.StartSignal(start_test_signal, create_flow).Next(this.signal_task)
    signal_task = flow.Signal(task_test_signal, signal_task).Next(this.end)
    end = flow.End()
