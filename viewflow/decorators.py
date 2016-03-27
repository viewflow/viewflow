import traceback
import functools

from django.db import transaction
from django.shortcuts import get_object_or_404

from .import types
from .activation import (
    StartActivation, ViewActivation, FuncActivation,
    AbstractJobActivation, STATUS
)
from .exceptions import FlowRuntimeError
from .fields import import_task_by_ref


def flow_func(task_loader=None, **lock_args):
    """Decorator for flow functions."""
    def decorator(func_or_cls):
        def wrapper(flow_task, *func_args, **func_kwargs):
            if isinstance(func_or_cls, type) and issubclass(func_or_cls, types.FlowFunc):
                receiver_cls = func_or_cls
            else:
                class FuncWrapper(types.FlowFunc):
                    def get_task(self, flow_task, *func_args, **func_kwargs):
                        return task_loader(flow_task, *func_args, **func_kwargs)

                    def __call__(self, activation, *func_args, **func_kwargs):
                        return func_or_cls(activation, *func_args, **func_kwargs)

                receiver_cls = FuncWrapper

            receiver = receiver_cls()

            task = receiver.get_task(flow_task, *func_args, **func_kwargs)
            if task is None:
                raise FlowRuntimeError(
                    "The task_loader didn't return any task for {}\n{}\n{}".format(
                        flow_task.name, func_args, func_kwargs))

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


def flow_job(**lock_args):
    """
    Decorator that prepares celery task for execution

    Makes celery job function with the following signature
    `(flow_task-strref, process_pk, task_pk, **kwargs)`

    Expects actual celery job function which has the following signature `(activation, **kwargs)`
    If celery task class implements activation interface, job function is
    called without activation instance `(**kwargs)`

    Process instance is locked only before and after the function execution.
    Please avoid any process state modification during the celery job.
    """
    class flow_task_decorator(object):
        def __init__(self, func, activation=None):
            self.func = func
            self.activation = activation
            functools.update_wrapper(self, func)

        def __call__(self, *args, **kwargs):
            flow_task_strref = kwargs.pop('flow_task_strref') if 'flow_task_strref' in kwargs else args[0]
            process_pk = kwargs.pop('process_pk') if 'process_pk' in kwargs else args[1]
            task_pk = kwargs.pop('task_pk') if 'task_pk' in kwargs else args[2]

            flow_task = import_task_by_ref(flow_task_strref)

            # start
            lock = flow_task.flow_cls.lock_impl(flow_task.flow_cls.instance, **lock_args)
            with lock(flow_task.flow_cls, process_pk):
                try:
                    task = flow_task.flow_cls.task_cls.objects.get(pk=task_pk)
                    if task.status == STATUS.CANCELED:
                        return
                except flow_task.flow_cls.task_cls.DoesNotExist:
                    # There was rollback on job task created transaction,
                    # we don't need to do the job
                    return
                else:
                    activation = self.activation if self.activation else flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    activation.start()

            # execute
            try:
                if self.activation:
                    result = self.func(**kwargs)
                else:
                    result = self.func(activation, **kwargs)
            except Exception as exc:
                # mark as error
                with lock(flow_task.flow_cls, process_pk):
                    task = flow_task.flow_cls.task_cls.objects.get(pk=task_pk)
                    activation = self.activation if self.activation else flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    activation.error(comments="{}\n{}".format(exc, traceback.format_exc()))
                raise
            else:
                # mark as done
                with lock(flow_task.flow_cls, process_pk):
                    task = flow_task.flow_cls.task_cls.objects.get(pk=task_pk)
                    activation = self.activation if self.activation else flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    activation.done()

                return result

        def __get__(self, instance, instancetype):
            """
            Bound methods called with self instance
            """
            if instance is None:
                return self

            func = self.func.__get__(instance, type)
            activation = instance if isinstance(instance, AbstractJobActivation) else None

            return self.__class__(func, activation=activation)

    return flow_task_decorator


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
            if isinstance(func_or_cls, type) and issubclass(func_or_cls, types.Receiver):
                receiver_cls = func_or_cls
            else:
                class FuncWrapper(types.Receiver):
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
                if isinstance(receiver, FuncActivation):
                    receiver.initialize(flow_task, task)
                    receiver(**signal_kwargs)
                else:
                    activation = flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    receiver(activation, **signal_kwargs)

        return wrapper

    return decorator


def flow_start_view():
    """
    Decorator for start views, creates and initializes start activation

    Expects view with the signature `(request, activation, **kwargs)`
    or CBV view that implements ViewActivation, in this case, dispatch
    would be called with `(request, **kwargs)`

    Returns `(request, flow_task, **kwargs)`
    """
    class StartViewDecorator(object):
        def __init__(self, func, activation=None):
            self.func = func
            self.activation = activation
            functools.update_wrapper(self, func)

        def __call__(self, request, flow_cls, flow_task, **kwargs):
            if self.activation:
                self.activation.initialize(flow_task, None)
                with transaction.atomic():
                    return self.func(request, **kwargs)
            else:
                activation = flow_task.activation_cls()
                activation.initialize(flow_task, None)
                with transaction.atomic():
                    return self.func(request, activation, **kwargs)

        def __get__(self, instance, instancetype):
            """
            If we decorate method on CBV that implements StartActivation interface,
            no custom activation is required.
            """
            if instance is None:
                return self

            func = self.func.__get__(instance, type)
            activation = instance if isinstance(instance, StartActivation) else None

            return self.__class__(func, activation=activation)

    return StartViewDecorator


def flow_view(**lock_args):
    """
    Decorator that locks and runs the flow view in transaction.

    Expects view with the signature `(request, activation, **kwargs)`
    or CBV view that implements TaskActivation, in this case, dispatch
    with would be called with `(request, **kwargs)`

    Returns `(request, flow_task, process_pk, task_pk, **kwargs)`
    """
    class flow_view_decorator(object):
        def __init__(self, func, activation=None):
            self.func = func
            self.activation = activation
            functools.update_wrapper(self, func)

        def __call__(self, request, flow_cls, flow_task, process_pk, task_pk, **kwargs):
            lock = flow_task.flow_cls.lock_impl(flow_task.flow_cls.instance, **lock_args)
            with lock(flow_task.flow_cls, process_pk):
                task = get_object_or_404(flow_task.flow_cls.task_cls._default_manager, pk=task_pk)

                if self.activation:
                    """
                    Class-based view that implements TaskActivation interface
                    """
                    self.activation.initialize(flow_task, task)
                    return self.func(request, **kwargs)
                else:
                    """
                    Function based view or CBV without TaskActvation interface implementation
                    """
                    activation = flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    return self.func(request, activation, **kwargs)

        def __get__(self, instance, instancetype):
            """
            If we decorate method on CBV that implements StartActivation interface,
            no custom activation is required.
            """
            if instance is None:
                return self

            func = self.func.__get__(instance, type)
            activation = instance if isinstance(instance, ViewActivation) else None

            return self.__class__(func, activation=activation)

    return flow_view_decorator
