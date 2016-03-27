from .. import base, mixins
from ..activation import StartActivation, FuncActivation


class StartSignal(mixins.TaskDescriptionMixin,
                  mixins.NextNodeMixin,
                  mixins.DetailsViewMixin,
                  mixins.UndoViewMixin,
                  mixins.CancelViewMixin,
                  base.Event):

    task_type = 'START'
    activation_cls = StartActivation

    def __init__(self, signal, receiver, sender=None, **kwargs):
        self.signal = signal
        self.receiver = receiver
        self.sender = sender

        super(StartSignal, self).__init__(**kwargs)

    def on_signal(self, **signal_kwargs):
        if isinstance(self.receiver, type) and issubclass(self.receiver, StartActivation):
            receiver = self.receiver()
            receiver.initialize(self, None)
            receiver(**signal_kwargs)
        else:
            activation = self.activation_cls()
            activation.initialize(self, None)
            self.receiver(activation, **signal_kwargs)

    def ready(self):
        self.signal.connect(
            self.on_signal, sender=self.sender,
            dispatch_uid="viewflow.flow.signal/{}.{}.{}".format(
                self.flow_cls.__module__, self.flow_cls.__name__, self.name))


class Signal(mixins.TaskDescriptionMixin,
             mixins.NextNodeMixin,
             mixins.DetailsViewMixin,
             mixins.UndoViewMixin,
             mixins.CancelViewMixin,
             base.Event):

    task_type = 'FUNC'
    activation_cls = FuncActivation

    def __init__(self, signal, receiver, sender=None, **kwargs):
        self.signal = signal
        self.receiver = receiver
        self.sender = sender
        super(Signal, self).__init__(**kwargs)

    def on_signal(self, **signal_kwargs):
        self.receiver(self, **signal_kwargs)

    def ready(self):
        self.signal.connect(
            self.on_signal, sender=self.sender,
            dispatch_uid="viewflow.flow.signal/{}.{}.{}".format(
                self.flow_cls.__module__, self.flow_cls.__name__, self.name))
