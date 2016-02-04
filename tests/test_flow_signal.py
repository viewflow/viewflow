from django.dispatch import Signal
from django.test import TestCase

from viewflow import flow
from viewflow.base import Flow, this
from viewflow.flow.signal import Receiver


class Test(TestCase):
    def test_signal_usecase(self):
        start_test_signal.send(sender=self)
        process = SignalFlow.process_cls.objects.get()
        task_test_signal.send(sender=self, process=process)

        tasks = process.task_set.all()
        self.assertEqual(3, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))

    def test_signal_ignore_activation(self):
        start_ignorable_test_signal.send(sender=self)
        process = SignalFlow.process_cls.objects.get()
        ignorable_test_signal.send(sender=self, process=process, ignore_me=True)

        active_tasks = process.active_tasks()
        self.assertEqual(1, len(active_tasks))

        ignorable_test_signal.send(sender=self, process=process, ignore_me=False)
        tasks = process.task_set.all()
        self.assertEqual(3, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))


start_test_signal = Signal()
start_ignorable_test_signal = Signal()
task_test_signal = Signal(providing_args=["process"])
ignorable_test_signal = Signal(providing_args=["process", "ignore_me"])


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


@flow.flow_signal(allow_skip_signals=True)
class IgnorableReceiver(Receiver):
    def get_task(self, flow_task, **kwargs):
        if kwargs['ignore_me']:
            return None
        return kwargs['process'].get_task(IgnorableSignalFlow.signal_task)

    def __call__(self, activation, **signal_kwargs):
        activation.prepare()
        activation.done()


class IgnorableSignalFlow(Flow):
    start = flow.StartSignal(start_ignorable_test_signal, create_flow) \
        .Next(this.signal_task)
    signal_task = flow.Signal(ignorable_test_signal, IgnorableReceiver) \
        .Next(this.end)
    end = flow.End()
