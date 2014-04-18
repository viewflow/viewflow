from viewflow import flow, lock
from viewflow.base import Flow, this

from unit.tasks import dummy_job


@flow.flow_view()
def perform_task(request, activation):
    raise NotImplementedError


class SingleTaskFlow(Flow):
    start = flow.Start() \
        .Activate('task')
    task = flow.View(perform_task)\
        .Next('end')
    end = flow.End()


class AllTaskFlow(Flow):
    lock_impl = lock.cache_lock

    start = flow.Start().Activate(this.view)
    view = flow.View(perform_task).Next(this.job)
    job = flow.Job(dummy_job).Next(this.iff)
    iff = flow.If(lambda act: True).OnTrue(this.switch).OnFalse(this.switch)
    switch = flow.Switch().Default(this.split)
    split = flow.Split().Always(this.join)
    join = flow.Join().Next(this.first)
    first = flow.First().Of(this.end)
    end = flow.End()
