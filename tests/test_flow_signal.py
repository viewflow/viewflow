from django.conf.urls import include, url
from django.contrib.auth.models import User
from django.dispatch import Signal
from django.test import TestCase

from viewflow import flow, views
from viewflow.base import Flow, this
from viewflow.flow.signal import Receiver
from viewflow.signals import task_finished
from viewflow.test import FlowTest
from viewflow.views import ProcessView


class Test(TestCase):
    def test_signal_usecase(self):
        start_test_signal.send(sender=self)
        process = SignalFlow.process_cls.objects.get()
        task_test_signal.send(sender=self, process=process)

        user = User.objects.create(username="test")

        with FlowTest(SignalFlow) as flow:
            flow.Task(SignalFlow.task).User("test").Execute() \
                .Assert(lambda t: t.flow_task == SignalFlow.task,
                    "Returned task should be the executed one.")

        tasks = process.task_set.all()
        self.assertEqual(4, tasks.count())
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
    signal_task = flow.Signal(task_test_signal, signal_task).Next(this.task)
    task = flow.View(ProcessView, fields=[]).Next(this.end)
    end = flow.End()


def create_other_flow(activation, **kwargs):
    process = kwargs['process']
    task = kwargs['task']
    if task.flow_task == SignalFlow.task:
        activation.prepare()
        activation.done()


class OtherFlow(Flow):
    start_signal = flow.StartSignal(task_finished, create_other_flow, sender=SignalFlow).Next(this.end)
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


urlpatterns = [
    url(r'^signal/', include([
        SignalFlow.instance.urls,
        url('^details/(?P<process_pk>\d+)/$', views.ProcessDetailView.as_view(), name='details'),
    ], namespace=SignalFlow.instance.namespace), {'flow_cls': SignalFlow}),
]


try:
    from django.test import override_settings
    Test = override_settings(ROOT_URLCONF=__name__)(Test)
except ImportError:
    """
    django 1.6
    """
    Test.urls = __name__
