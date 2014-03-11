from viewflow import flow
from viewflow.base import this, Flow
from viewflow.views import TaskView

from examples.onetwothree.models import StepProcess


class StepFlow(Flow):
    process_cls = StepProcess

    start = flow.Start() \
        .Activate(this.one)

    one = flow.View(TaskView.as_view(fields=['one'])) \
        .Next(this.two)

    two = flow.View(TaskView.as_view(fields=['two'])) \
        .Next(this.three)

    three = flow.View(TaskView.as_view(fields=['three'])) \
        .Next(this.end)

    end = flow.End()
