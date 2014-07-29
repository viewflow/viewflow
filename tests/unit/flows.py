from viewflow import flow, lock
from viewflow.base import Flow, this

from .tasks import dummy_job, start_process, do_task
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
    job = flow.Job(dummy_job).Next(this.iff)
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
    job = flow.Job(dummy_job).Next(this.iff)
    iff = flow.If(lambda p: 2/(1-1)).OnTrue(this.end).OnFalse(this.end)
    end = flow.End()


class FailedGateFlow(Flow):
    """
    Test that failed If gate not reflects on finished job
    """
    lock_impl = lock.cache_lock

    start = flow.Start().Next(this.job)
    job = flow.Job(dummy_job).Next(this.iff)
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

    start = flow.StartSignal(test_start_flow, start_process) \
        .Next(this.task)
    task = flow.Signal(test_done_flow_task, do_task) \
        .Next(this.end)
    end = flow.End()
