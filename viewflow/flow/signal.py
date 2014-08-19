"""
django signals as part of flow
"""
import six

from viewflow.flow.base import Event, Edge
from viewflow.activation import StartActivation, TaskActivation


class StartSignal(Event):
    task_type = 'START'
    activation_cls = StartActivation

    def __init__(self, signal, receiver, sender=None, **kwargs):
        self.signal = signal
        self.receiver = receiver
        self.sender = sender

        super(StartSignal, self).__init__(**kwargs)
        self._activate_next = []

    def _outgoing(self):
        for next_node in self._activate_next:
            yield Edge(src=self, dst=next_node, edge_class='next')

    def on_signal(self, **signal_kwargs):
        if isinstance(self.receiver, type) and issubclass(self.receiver, StartActivation):
            receiver = self.receiver()
            receiver.initialize(self)
            receiver(**signal_kwargs)
        else:
            activation = self.activation_cls()
            activation.initialize(self)
            self.receiver(activation, **signal_kwargs)

    def ready(self):
        self.signal.connect(
            self.on_signal, sender=self.sender,
            dispatch_uid="viewflow.flow.signal/{}.{}.{}".format(
                self.flow_cls.__module__, self.flow_cls.__name__, self.name))

    def Next(self, node):
        self._activate_next.append(node)
        return self

    def has_perm(self, user):
        return False


class Receiver(object):
    def get_task(self, flow_task, **signal_kwargs):
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


def flow_signal(task_loader=None, **lock_args):
    """
    Decorator for flow signal receivers
    """
    def decorator(func_or_cls):
        def wrapper(flow_task, **signal_kwargs):
            if isinstance(func_or_cls, type) and issubclass(func_or_cls, Receiver):
                receiver_cls = func_or_cls
            else:
                class FuncWrapper(Receiver):
                    def get_task(self, flow_task, **kwargs):
                        return task_loader(flow_task, kwargs['sender'])

                    def __call__(self, activation, *args, **kwargs):
                        return func_or_cls(activation, *args, **kwargs)

                receiver_cls = FuncWrapper

            receiver = receiver_cls()
            task = receiver.get_task(flow_task, **signal_kwargs)
            lock_func = six.get_unbound_function(flow_task.flow_cls.lock_impl)
            lock = lock_func(**lock_args)

            with lock(flow_task, task.process_id):
                task = flow_task.flow_cls.task_cls._default_manager.get(pk=task.pk)
                if isinstance(receiver, TaskActivation):
                    receiver.initialize(flow_task, task)
                    receiver(**signal_kwargs)
                else:
                    activation = flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    receiver(activation, **signal_kwargs)

        return wrapper

    return decorator


class Signal(Event):
    """
    Executes code on django signal

    Example:

        create_model = flow.Signal(post_create, my_receiver, sender=MyModelCls)

    """
    task_type = 'FUNC'
    activation_cls = TaskActivation

    def __init__(self, signal, receiver, sender=None, **kwargs):
        self.signal = signal
        self.receiver = receiver
        self.sender = sender
        super(Signal, self).__init__(**kwargs)
        self._activate_next = []

    def _outgoing(self):
        for next_node in self._activate_next:
            yield Edge(src=self, dst=next_node, edge_class='next')

    def on_signal(self, **signal_kwargs):
        self.receiver(self, **signal_kwargs)

    def ready(self):
        self.signal.connect(
            self.on_signal, sender=self.sender,
            dispatch_uid="viewflow.flow.signal/{}.{}.{}".format(
                self.flow_cls.__module__, self.flow_cls.__name__, self.name))

    def Next(self, node):
        self._activate_next.append(node)
        return self
