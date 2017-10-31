from .. import Event, ThisObject, mixins
from ..activation import StartActivation, FuncActivation
from ..exceptions import FlowRuntimeError


class StartSignal(mixins.TaskDescriptionMixin,
                  mixins.NextNodeMixin,
                  mixins.DetailViewMixin,
                  mixins.UndoViewMixin,
                  mixins.CancelViewMixin,
                  Event):
    """
    Start flow on a django signal receive.

    Example::

        class MyFlow(Flow):
            start = (
                flow.StartSignal(
                    post_save, this.start_flow,
                    sender=MyModelCls)
                .Next(this.approve)
            )

            ...

            @flow_start_signal
            def start_flow(self, activation, **signal_kwargs):
                activation.prepare()
                activation.done()
    """

    task_type = 'START'
    activation_class = StartActivation

    def __init__(self, signal, receiver, sender=None, **kwargs):
        """
        Instantiate a StartSignal task.

        :param signal: A django signal to connect
        :param receiver: Callable[activation, **kwargs]
        :param sender: Optional signal sender
        """
        self.signal = signal
        self.receiver = receiver
        self.sender = sender

        super(StartSignal, self).__init__(**kwargs)

    def on_signal(self, sender, **signal_kwargs):
        """Signal handler."""
        return self.receiver(sender=sender, flow_task=self, **signal_kwargs)

    def ready(self):
        """Resolve internal `this`-references. and subscribe to the signal."""
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
    """
    Execute a callback on a django signal receive.

    Example::

        class MyFlow(Flow):
            wait_for_receipt = (
                flow.Signal(
                    post_create, this.receipt_created,
                    sender=MyModelCls)
                .Next(this.approve)

            ...

            def receipt_created(self, activation, **signal_kwargs):
                activation.prepare()
                activation.process.receipt = signal_kwargs['instance']
                activation.done()
    """

    task_type = 'FUNC'
    activation_class = FuncActivation

    def __init__(self, signal, receiver, sender=None, task_loader=None, allow_skip=False, **kwargs):
        """
        Instantiate a Signal task.

        :param signal: A django signal to connect
        :param receiver: Callable[activation, **kwargs]
        :param sender: Optional signal sender
        :param task_loader: Callable[**kwargs] -> Task
        :param allow_skip: If True task_loader can return None if
                           signal could be skipped.

        You can skip a `task_loader` if the signal going to be
        sent with Task instance.
        """
        self.signal = signal
        self.receiver = receiver
        self.sender = sender
        self.task_loader = task_loader
        self.allow_skip = allow_skip
        super(Signal, self).__init__(**kwargs)

    def on_signal(self, sender, **signal_kwargs):
        """Signal handler."""
        if self.task_loader is None:
            if 'task' not in signal_kwargs:
                raise FlowRuntimeError('{} have no task_loader and got signal without task instance'.format(self.name))
            return self.receiver(sender=sender, **signal_kwargs)
        else:
            task = self.task_loader(self, sender=sender, **signal_kwargs)
            if task is None:
                if self.allow_skip is False:
                    raise FlowRuntimeError("The task_loader didn't return any task for {}\n{}".format(
                        self.name, signal_kwargs))
            else:
                return self.receiver(sender=sender, _task=task, **signal_kwargs)

    def ready(self):
        """Resolve internal `this`-references. and subscribe to the signal."""
        if isinstance(self.receiver, ThisObject):
            self.receiver = getattr(self.flow_class.instance, self.receiver.name)
        if isinstance(self.task_loader, ThisObject):
            self.task_loader = getattr(self.flow_class.instance, self.task_loader.name)

        self.signal.connect(
            self.on_signal, sender=self.sender,
            dispatch_uid="viewflow.flow.signal/{}.{}.{}".format(
                self.flow_class.__module__, self.flow_class.__name__, self.name))
