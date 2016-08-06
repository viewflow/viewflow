from django.dispatch import Signal
from django.utils.decorators import method_decorator
from django.test import TestCase

from viewflow import flow
from viewflow.base import Flow, this


class Test(TestCase):
    def test_signal_usecase(self):
        start_test_signal.send(sender=self)
        process = SignalFlow.process_class.objects.get()
        task_test_signal.send(sender=self, process=process)

        tasks = process.task_set.all()
        self.assertEqual(3, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))

    def test_signal_ignore_activation(self):
        start_ignorable_test_signal.send(sender=self)
        process = SignalFlow.process_class.objects.get()
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


@flow.flow_start_signal
def create_flow(sender, activation, **kwargs):
    activation.prepare()
    activation.done()
    return activation


@flow.flow_signal
def signal_task(activation, **kwargs):
    activation.prepare()
    activation.done()


class SignalFlow(Flow):
    start = (
        flow.StartSignal(
            start_test_signal, create_flow)
        .Next(this.signal_task)
    )

    signal_task = (
        flow.Signal(
            task_test_signal, signal_task,
            task_loader=this.get_signal_task)
        .Next(this.end)
    )

    end = flow.End()

    def get_signal_task(self, flow_task, **kwargs):
        return kwargs['process'].get_task(SignalFlow.signal_task)


class IgnorableSignalFlow(Flow):
    start = (
        flow.StartSignal(
            start_ignorable_test_signal, create_flow)
        .Next(this.signal_task)
    )

    signal_task = (
        flow.Signal(
            ignorable_test_signal, this.on_test_signal,
            task_loader=this.get_signal_task,
            allow_skip=True)
        .Next(this.end)
    )

    end = flow.End()

    def get_signal_task(self, flow_task, **kwargs):
        if kwargs['ignore_me']:
            return None
        return kwargs['process'].get_task(IgnorableSignalFlow.signal_task)

    @method_decorator(flow.flow_signal)
    def on_test_signal(self, activation, **signal_kwargs):
        activation.prepare()
        activation.done()
