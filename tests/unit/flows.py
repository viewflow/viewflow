from viewflow import flow
from viewflow.base import Flow


def perform_task(request, act_id):
    raise NotImplementedError


class SingleTaskFlow(Flow):
    start = flow.Start() \
        .Activate('task')
    task = flow.View(perform_task)\
        .Next('end')
    end = flow.End()
