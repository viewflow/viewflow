"""Functions and handlers as part of flow."""
import traceback
from django.db import transaction
from django.utils.timezone import now

from ..activation import Activation, StartActivation, STATUS, context
from ..exceptions import FlowRuntimeError
from . import base


class StartFunction(base.TaskDescriptionMixin,
                    base.NextNodeMixin,
                    base.DetailsViewMixin,
                    base.Event):

    """
    StartNode that can be executed within you code.

    Example::

        def create_request(activation, **kwargs):
            activation.prepare()
            # Your custom code
            activation.done()

        class MyFlow(Flow):
            start = flow.StartFunction(create_request)

        MyFlow.create_request.run(**kwargs)

    .. note::

        Any kwarg you pass of the run call will be passed to the function.

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
        """Activate all outgoing edges."""
        if self.flow_task._next:
            self.flow_task._next.activate(prev_activation=self, token=self.task.token)

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        """Instantiate new task."""
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
    """Decorator for flow functions."""
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
                    return receiver(*func_args, **func_kwargs)
                else:
                    activation = flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    return receiver(activation, *func_args, **func_kwargs)

        return wrapper

    return decorator


class Function(base.TaskDescriptionMixin,
               base.NextNodeMixin,
               base.DetailsViewMixin,
               base.Event):

    """
    Node that can be executed within you code.

    Example::

        def my_function(activation, **kwargs):
            activation.prepare()
            # Your custom code
            activation.done()

        class MyFlow(Flow):
            my_task = flow.Function(my_function)

        MyFlow.my_task.run(**kwargs)

    .. note::

        Any kwarg you pass of the run call will be passed to the function.

    """

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

    def run(self, *args, **kwargs):
        return self.func(self, *args, **kwargs)


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

    @Activation.status.transition(source=STATUS.ERROR)
    def retry(self):
        """
        Retry the next node calculation and activation
        """
        self.perform.original()

    @Activation.status.transition(source=[STATUS.ERROR, STATUS.DONE], target=STATUS.NEW)
    def undo(self):
        """
        Undo the task
        """
        super(HandlerActivation, self).undo.original()

    @Activation.status.transition(source=STATUS.DONE)
    def activate_next(self):
        """Activate all outgoing edges."""
        if self.flow_task._next:
            self.flow_task._next.activate(prev_activation=self, token=self.task.token)

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        """Instantiate new task."""
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


class Handler(base.TaskDescriptionMixin,
              base.NextNodeMixin,
              base.DetailsViewMixin,
              base.Event):

    """
    Node that can be executed automatically after task was created.

    In difference to :class:`.Function` a :class:`.Handler` is not explicitly called
    in code, but executes automatically.

    Example::

        def my_handler(activation):
            # Your custom code
            pass

        class MyFlow(Flow):
            previous_task = flow.View(ProcessView) \
                .Next(this.my_task)

            my_task = flow.Function(my_handler) \
                .Next(this.End)

            end = flow.End()

    .. note::

        You don't need to call ``prepare()`` or ``done()`` on the
        activation in you handler callback.

    """

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
