from viewflow import flow
from viewflow.base import this, Flow

from examples.onetwothree.models import StepProcess
from examples.onetwothree import views


class StepFlow(Flow):
    process_cls = StepProcess

    start = flow.Start() \
        .Activate(this.one)

    one = flow.View() \
        .Next(this.two)

    two = flow.View(views.two) \
        .Next(this.three)

    three = flow.View(views.three) \
        .Next(this.end)

    end = flow.End()
