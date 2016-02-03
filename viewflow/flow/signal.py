"""Django signals as part of flow."""
from ..activation import StartActivation
from ..exceptions import FlowRuntimeError
from . import base, func


class StartSignal(base.TaskDescriptionMixin,
                  base.NextNodeMixin,
                  base.DetailsViewMixin,
                  base.Event):

    """
    StartNode that connects to a django signal.

    Example::

        def my_start_receiver(activation, **signal_kwargs):
            activation.prepare()
            # You custom code
            activation.done()

        class MyFlow(Flow):
            start = flow.StartSignal(post_save, my_start_receiver, sender=MyModelCls)

    .. note::

        The first argument of your receiver will be the activation.

    """

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


class Receiver(object):

    """
    Flow signal receiver that gets the signaled task form the kwargs.

    Subclasses must implement :method:`.get_task` and :method:`.__call__`.

    Example::

        @flow_signal()
        class MyReceiver(Receiver):
            def get_task(self, flow_task, **signal_kwargs):
                return kwargs['process'].get_task(flow_task)

            def __call__(self, activation, **signal_kwargs):
                activation.prepare()
                activation.done()

    .. note::

        In this example your signal will need to be send
        with ``process`` as a kwarg.

    """

    def get_task(self, flow_task, **signal_kwargs):
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


def flow_signal(task_loader=None, allow_skip_signals=False, **lock_args):
    """
    Decorator providing a flow signal receiver with the activation.

    Args:
        task_loader (callable): callable that returns the signaled flow_task

    The decorator can be used ether with a callable defining a `task_loader`
    or with a :class:`.Receiver` subclass and no `task_loader`.

    if `allow_skip_signals` is True, flow_task will not be proceed if task_loader
    returns None.

    Example::

        @flow_signal(task_loader=lambda flow_task, **kwargs: kwargs['process'].get_task(flow_task))
        def my_receiver(activation, **kwargs):
            activation.prepare()
            activation.done()

    or::

        @flow_signal()
        class MyReceiver(Receiver):
            def get_task(self, flow_task, **signal_kwargs):
                return kwargs['process'].get_task(flow_task)

            def __call__(self, activation, **signal_kwargs):
                activation.prepare()
                activation.done()

    .. note::

        In both examples your signal will need to be send
        with ``process`` as a kwarg.

    """
    def decorator(func_or_cls):
        def wrapper(flow_task, **signal_kwargs):
            if isinstance(func_or_cls, type) and issubclass(func_or_cls, Receiver):
                receiver_cls = func_or_cls
            else:
                class FuncWrapper(Receiver):
                    def get_task(self, flow_task, **kwargs):
                        return task_loader(flow_task, **kwargs)

                    def __call__(self, activation, *args, **kwargs):
                        return func_or_cls(activation, *args, **kwargs)

                receiver_cls = FuncWrapper

            receiver = receiver_cls()
            task = receiver.get_task(flow_task, **signal_kwargs)
            if task is None:
                if allow_skip_signals:
                    return
                else:
                    raise FlowRuntimeError(
                        "The task_loader didn't return any task for {}\n{}".format(
                            flow_task.name, signal_kwargs))

            lock = flow_task.flow_cls.lock_impl(flow_task.flow_cls.instance, **lock_args)
            with lock(flow_task.flow_cls, task.process_id):
                task = flow_task.flow_cls.task_cls._default_manager.get(pk=task.pk)
                if isinstance(receiver, func.FuncActivation):
                    receiver.initialize(flow_task, task)
                    receiver(**signal_kwargs)
                else:
                    activation = flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    receiver(activation, **signal_kwargs)

        return wrapper

    return decorator


class Signal(base.TaskDescriptionMixin,
             base.NextNodeMixin,
             base.DetailsViewMixin,
             base.Event):

    """
    Node that connects to a django signal.

    Example::

        create_model = flow.Signal(post_create, my_receiver, sender=MyModelCls)

    .. note::

        Other than the :class:`.StartSignal` you will need to provide activation
        for your receiver yourself. This can be done using the :func:`.flow_signal`
        decorator.

    """

    task_type = 'FUNC'
    activation_cls = func.FuncActivation

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
