from viewflow import flow, lock
from viewflow.base import Flow, this
from viewflow.contrib import celery


from . import tasks
from .models import TestProcess
from .signals import test_start_flow, test_done_flow_task


@flow.flow_view()
def perform_task(request, activation):
    raise NotImplementedError


class SingleTaskFlow(Flow):
    lock_impl = lock.cache_lock

    start = flow.Start() \
        .Next('task')
    task = flow.View(perform_task)\
        .Next('end')
    end = flow.End()


class AllTaskFlow(Flow):
    lock_impl = lock.cache_lock

    start = flow.Start().Next(this.view)
    view = flow.View(perform_task).Next(this.job)
    job = celery.Job(tasks.dummy_job).Next(this.iff)
    iff = flow.If(lambda act: True).OnTrue(this.switch).OnFalse(this.switch)
    switch = flow.Switch().Default(this.split)
    split = flow.Split().Always(this.join)
    join = flow.Join().Next(this.first)
    first = flow.First().Of(this.end)
    end = flow.End()


class FailedJobFlow(Flow):
    """
    Test that failed job gate stored task in error state
    """
    lock_impl = lock.cache_lock

    start = flow.Start().Next(this.job)
    job = celery.Job(tasks.dummy_job).Next(this.iff)
    iff = flow.If(lambda p: 2/(1-1)).OnTrue(this.end).OnFalse(this.end)
    end = flow.End()


class FailedGateFlow(Flow):
    """
    Test that failed If gate not reflects on finished job
    """
    lock_impl = lock.cache_lock

    start = flow.Start().Next(this.job)
    job = celery.Job(tasks.dummy_job).Next(this.iff)
    iff = flow.If(lambda p: 2/0).OnTrue(this.end).OnFalse(this.end)
    end = flow.End()


class AutoPermissionsFlow(Flow):
    process_cls = TestProcess

    start = flow.Start() \
        .Permission(auto_create=True) \
        .Next(this.end)

    end = flow.End()


class SignalFlow(Flow):
    process_cls = TestProcess

    start = flow.StartSignal(test_start_flow, tasks.start_process) \
        .Next(this.task)
    task = flow.Signal(test_done_flow_task, tasks.do_signal_task) \
        .Next(this.end)
    end = flow.End()


class FunctionFlow(Flow):
    process_cls = TestProcess

    start = flow.StartFunction(tasks.start_process) \
        .Next(this.task1)

    task1 = flow.Handler(tasks.do_handler_task) \
        .Next(this.task2)

    task2 = flow.Function(tasks.do_func_task) \
        .Next(this.end)

    end = flow.End()


class DefaultProcessFunctionFlow(Flow):
    start = flow.StartFunction(tasks.start_process) \
        .Next(this.end)
    end = flow.End()
