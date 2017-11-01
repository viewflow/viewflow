import sys
import traceback
import functools

from django.db import transaction
from django.shortcuts import get_object_or_404

from .activation import STATUS
from .fields import import_task_by_ref


def flow_start_func(func):
    """Decorator for flow functions."""
    @transaction.atomic
    @functools.wraps(func)
    def _wrapper(flow_task, *args, **kwargs):
        exc = True
        try:
            try:
                activation = flow_task.activation_class()
                activation.initialize(flow_task, None)
                return func(activation, *args, **kwargs)
            except:
                exc = False
                if activation.lock:
                    activation.lock.__exit__(*sys.exc_info())
                raise
        finally:
            if exc and activation.lock:
                activation.lock.__exit__(None, None, None)
    return _wrapper


def flow_func(func):
    """
    Decorator for flow functions.

    Expects function that gets activation instance as the first parameter.
    Returns function that expects task instance as the first parameter instead.
    """
    @transaction.atomic
    @functools.wraps(func)
    def _wrapper(task, *args, **kwargs):
        flow_task = task.flow_task
        flow_class = flow_task.flow_class

        lock = flow_class.lock_impl(flow_class.instance)
        with lock(flow_class, task.process_id):
            task = flow_class.task_class._default_manager.get(pk=task.pk, process_id=task.process_id)
            activation = flow_task.activation_class()
            activation.initialize(flow_task, task)
            return func(activation, *args, **kwargs)
    return _wrapper


def flow_job(func):
    """
    Decorator that prepares celery task for execution.

    Makes celery job function with the following signature
    `(flow_task-strref, process_pk, task_pk, **kwargs)`.

    Expects actual celery job function which has the following signature `(activation, **kwargs)`.
    If celery task class implements activation interface, job function is
    called without activation instance `(**kwargs)`.

    Process instance is locked only before and after the function execution.
    Please avoid any process state modification during the celery job.
    """
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        flow_task_strref = kwargs.pop('flow_task_strref') if 'flow_task_strref' in kwargs else args[0]
        process_pk = kwargs.pop('process_pk') if 'process_pk' in kwargs else args[1]
        task_pk = kwargs.pop('task_pk') if 'task_pk' in kwargs else args[2]
        flow_task = import_task_by_ref(flow_task_strref)

        lock = flow_task.flow_class.lock_impl(flow_task.flow_class.instance)

        # start
        with transaction.atomic(), lock(flow_task.flow_class, process_pk):
            try:
                task = flow_task.flow_class.task_class.objects.get(pk=task_pk, process_id=process_pk)
                if task.status == STATUS.CANCELED:
                    return
            except flow_task.flow_class.task_class.DoesNotExist:
                # There was rollback on job task created transaction,
                # we don't need to do the job
                return
            else:
                activation = flow_task.activation_class()
                activation.initialize(flow_task, task)
                if task.status == STATUS.SCHEDULED:
                    activation.start()
                else:
                    activation.restart()

        # execute
        try:
            result = func(activation, **kwargs)
        except Exception as exc:
            # mark as error
            with transaction.atomic(), lock(flow_task.flow_class, process_pk):
                task = flow_task.flow_class.task_class.objects.get(pk=task_pk, process_id=process_pk)
                activation = flow_task.activation_class()
                activation.initialize(flow_task, task)
                activation.error(comments="{}\n{}".format(exc, traceback.format_exc()))
            raise
        else:
            # mark as done
            with transaction.atomic(), lock(flow_task.flow_class, process_pk):
                task = flow_task.flow_class.task_class.objects.get(pk=task_pk, process_id=process_pk)
                activation = flow_task.activation_class()
                activation.initialize(flow_task, task)
                activation.done()

            return result

    return _wrapper


def flow_start_signal(handler):
    """Decorator provides a flow signal receiver with the activation."""
    @transaction.atomic
    @functools.wraps(handler)
    def _wrapper(sender, flow_task=None, **signal_kwargs):
        exc = True
        try:
            try:
                activation = flow_task.activation_class()
                activation.initialize(flow_task, None)
                return handler(sender=sender, activation=activation, **signal_kwargs)
            except:
                exc = False
                if activation.lock:
                    activation.lock.__exit__(*sys.exc_info())
                raise
        finally:
            if exc and activation.lock:
                activation.lock.__exit__(None, None, None)
    return _wrapper


def flow_signal(handler):
    """Decorator provides a flow signal receiver with the activation."""
    @transaction.atomic
    @functools.wraps(handler)
    def _wrapper(sender, _task=None, **signal_kwargs):
        task = _task
        flow_task = task.flow_task
        flow_class = flow_task.flow_class

        lock = flow_class.lock_impl(flow_class.instance)
        with lock(flow_class, task.process_id):
            task = flow_class.task_class._default_manager.get(pk=task.pk, process_id=task.process_id)
            activation = flow_task.activation_class()
            activation.initialize(flow_task, task)
            return handler(sender=sender, activation=activation, **signal_kwargs)
    return _wrapper


def flow_start_view(view):
    """
    Decorator for start views, creates and initializes start activation.

    Expects view with the signature `(request, **kwargs)`.
    Returns view with the signature `(request, flow_class, flow_task, **kwargs)`.
    """
    @transaction.atomic
    @functools.wraps(view)
    def _wrapper(request, flow_class, flow_task, **kwargs):
        exc = True
        try:
            try:
                activation = flow_task.activation_class()
                activation.initialize(flow_task, None)

                request.activation = activation
                request.process = activation.process
                request.task = activation.task
                return view(request, **kwargs)
            except:
                exc = False
                if activation.lock:
                    activation.lock.__exit__(*sys.exc_info())
                raise
        finally:
            if exc and activation.lock:
                activation.lock.__exit__(None, None, None)

    return _wrapper


def flow_view(view):
    """
    Decorator that locks and runs the flow view in transaction.

    Expects view with the signature `(request, **kwargs)`.
    Returns view with the signature `(request, flow_class, flow_task, process_pk, task_pk, **kwargs)`.
    """
    @transaction.atomic
    @functools.wraps(view)
    def _wrapper(request, flow_class, flow_task, process_pk, task_pk, **kwargs):
        lock = flow_task.flow_class.lock_impl(flow_class.instance)
        with lock(flow_class, process_pk):
            task = get_object_or_404(flow_task.flow_class.task_class._default_manager, pk=task_pk, process_id=process_pk)
            activation = flow_task.activation_class()
            activation.initialize(flow_task, task)

            request.activation = activation
            request.process = activation.process
            request.task = activation.task

            return view(request, **kwargs)
    return _wrapper
