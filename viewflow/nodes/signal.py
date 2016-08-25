from .. import Event, ThisObject, mixins
from ..activation import StartActivation, FuncActivation
from ..exceptions import FlowRuntimeError


class StartSignal(mixins.TaskDescriptionMixin,
                  mixins.NextNodeMixin,
                  mixins.DetailViewMixin,
                  mixins.UndoViewMixin,
                  mixins.CancelViewMixin,
                  Event):

    task_type = 'START'
    activation_class = StartActivation

    def __init__(self, signal, receiver, sender=None, **kwargs):
        self.signal = signal
        self.receiver = receiver
        self.sender = sender

        super(StartSignal, self).__init__(**kwargs)

    def on_signal(self, sender, **signal_kwargs):
        return self.receiver(sender=sender, flow_task=self, **signal_kwargs)

    def ready(self):
        if isinstance(self.receiver, ThisObject):
            self.receiver = getattr(self.flow_class.instance, self.receiver.name)

        self.signal.connect(
            self.on_signal, sender=self.sender,
            dispatch_uid="viewflow.flow.signal/{}.{}.{}".format(
                self.flow_class.__module__, self.flow_class.__name__, self.name))


class Signal(mixins.TaskDescriptionMixin,
             mixins.NextNodeMixin,
             mixins.DetailViewMixin,
             mixins.UndoViewMixin,
             mixins.CancelViewMixin,
             Event):

    task_type = 'FUNC'
    activation_class = FuncActivation

    def __init__(self, signal, receiver, sender=None, task_loader=None, allow_skip=False, **kwargs):
        self.signal = signal
        self.receiver = receiver
        self.sender = sender
        self.task_loader = task_loader
        self.allow_skip = allow_skip
        super(Signal, self).__init__(**kwargs)

    def on_signal(self, sender, **signal_kwargs):
        if self.task_loader is None:
            if 'task' not in signal_kwargs:
                raise FlowRuntimeError('{} have no task_loader and got signal without task instance', self.name)
            return self.receiver(sender=sender, **signal_kwargs)
        else:
            task = self.task_loader(self, sender=sender, **signal_kwargs)
            if task is None:
                if self.allow_skip is False:
                    raise FlowRuntimeError("The task_loader didn't return any task for {}\n{}".format(
                        self.name, signal_kwargs))
            else:
                return self.receiver(sender=sender, task=task, **signal_kwargs)

    def ready(self):
        if isinstance(self.receiver, ThisObject):
            self.receiver = getattr(self.flow_class.instance, self.receiver.name)
        if isinstance(self.task_loader, ThisObject):
            self.task_loader = getattr(self.flow_class.instance, self.task_loader.name)

        self.signal.connect(
            self.on_signal, sender=self.sender,
            dispatch_uid="viewflow.flow.signal/{}.{}.{}".format(
                self.flow_class.__module__, self.flow_class.__name__, self.name))
