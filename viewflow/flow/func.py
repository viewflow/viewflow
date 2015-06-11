"""
Function handlers as part of flow
"""
import traceback
from django.db import transaction
from django.utils.timezone import now

from ..activation import Activation, StartActivation, STATUS, context
from ..exceptions import FlowRuntimeError
from . import base


class StartFunction(base.NextNodeMixin, base.DetailsViewMixin, base.Event):
    """
    def create_requst(activation):
        activation.prepare()
        activation.done()

    class MyFlow(Flow):
        start_request = flow.StartFunction(create_request)

    MyFlow.create_request.run()
    """

    task_type = 'START'
    activation_cls = StartActivation

    def __init__(self, func=None, **kwargs):
        self._func = func
        super(StartFunction, self).__init__(**kwargs)

    @property
    def func(self):
        if self._func is not None:
            return self._func
        else:
            func_name = '{}_func'.format(self.name)
            func_impl = getattr(self.flow_cls.instance, func_name, None)
            if func_impl:
                return func_impl
            else:
                def default_start_func(activation):
                    activation.prepare()
                    activation.done()
                    return activation
                return default_start_func

    def run(self, *args, **kwargs):
        if isinstance(self.func, type) and issubclass(self.func, StartActivation):
            receiver = self.func()
            receiver.initialize(self, None)
            return receiver(*args, **kwargs)
        else:
            activation = self.activation_cls()
            activation.initialize(self, None)
            return self.func(activation, *args, **kwargs)


class FuncActivation(Activation):
    @Activation.status.transition(source=STATUS.NEW, target=STATUS.PREPARED)
    def prepare(self):
        self.task.started = now()

    @Activation.status.transition(source=STATUS.PREPARED, target=STATUS.DONE)
    def done(self):
        self.task.finished = now()
        self.task.save()

        self.activate_next()

    @Activation.status.transition(source=STATUS.DONE)
    def activate_next(self):
        """
        Activate all outgoing edges.
        """
        self.flow_task._next.activate(prev_activation=self, token=self.task.token)

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        """
        Instantiate new task
        """
        task = flow_task.flow_cls.task_cls(
            process=prev_activation.process,
            flow_task=flow_task,
            token=token)

        task.save()
        task.previous.add(prev_activation.task)

        activation = cls()
        activation.initialize(flow_task, task)

        return activation


class FlowFunc(object):
    def get_task(self, flow_task, *func_args, **func_kwars):
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        raise NotImplementedError


def flow_func(task_loader=None, **lock_args):
    """
    Decorator for flow functions
    """
    def decorator(func_or_cls):
        def wrapper(flow_task, *func_args, **func_kwargs):
            if isinstance(func_or_cls, type) and issubclass(func_or_cls, FlowFunc):
                receiver_cls = func_or_cls
            else:
                class FuncWrapper(FlowFunc):
                    def get_task(self, flow_task, *func_args, **func_kwargs):
                        return task_loader(flow_task, *func_args, **func_kwargs)

                    def __call__(self, activation, *func_args, **func_kwargs):
                        return func_or_cls(activation, *func_args, **func_kwargs)

                receiver_cls = FuncWrapper

            receiver = receiver_cls()

            task = receiver.get_task(flow_task, *func_args, **func_kwargs)
            lock = flow_task.flow_cls.lock_impl(flow_task.flow_cls.instance, **lock_args)

            with lock(flow_task.flow_cls, task.process_id):
                task = flow_task.flow_cls.task_cls._default_manager.get(pk=task.pk)
                if isinstance(receiver, FuncActivation):
                    receiver.initialize(flow_task, task)
                    receiver(*func_args, **func_kwargs)
                else:
                    activation = flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    receiver(activation, *func_args, **func_kwargs)

        return wrapper

    return decorator


class Function(base.NextNodeMixin, base.DetailsViewMixin, base.Event):
    task_type = 'FUNC'
    activation_cls = FuncActivation

    def __init__(self, func=None, **kwargs):
        self._func = func
        super(Function, self).__init__(**kwargs)

    @property
    def func(self):
        if self._func is not None:
            return self._func
        else:
            func_name = '{}_func'.format(self.name)
            func_impl = getattr(self.flow_cls.instance, func_name, None)
            if func_impl:
                return func_impl
            else:
                def default_start_func(activation):
                    activation.prepare()
                    activation.done()
                    return activation
                return default_start_func

    def run(self, *args, **kwargs):
        self.func(self, *args, **kwargs)


class HandlerActivation(Activation):
    def execute(self):
        self.flow_task.handler(self)

    @Activation.status.transition(source=STATUS.NEW)
    def perform(self):
        try:
            self.task.started = now()

            with transaction.atomic(savepoint=True):
                self.execute()
                self.task.finished = now()
                self.set_status(STATUS.DONE)
                self.task.save()
                self.activate_next()
        except Exception as exc:
            if not context.propagate_exception:
                self.task.comments = "{}\n{}".format(exc, traceback.format_exc())
                self.task.finished = now()
                self.set_status(STATUS.ERROR)
                self.task.save()
            else:
                raise

    @Activation.status.transition(source=STATUS.DONE)
    def activate_next(self):
        """
        Activate all outgoing edges.
        """
        self.flow_task._next.activate(prev_activation=self, token=self.task.token)

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        """
        Instantiate new task
        """
        task = flow_task.flow_cls.task_cls(
            process=prev_activation.process,
            flow_task=flow_task,
            token=token)

        task.save()
        task.previous.add(prev_activation.task)

        activation = cls()
        activation.initialize(flow_task, task)
        activation.perform()

        return activation


class Handler(base.NextNodeMixin, base.DetailsViewMixin, base.Event):
    task_type = 'FUNC'
    activation_cls = HandlerActivation

    def __init__(self, handler=None, **kwargs):
        self._handler = handler
        super(Handler, self).__init__(**kwargs)

    @property
    def handler(self):
        if self._handler is not None:
            return self._handler
        else:
            handler_name = '{}_handler'.format(self.name)
            handler_impl = getattr(self.flow_cls.instance, handler_name, None)
            if handler_impl:
                return handler_impl
            raise FlowRuntimeError('Handler for {} not defined'.format(self.name))
