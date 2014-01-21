from viewflow import flow, this, Flow
from onetwothee import views


class StepFlow(Flow):
    start = flow.Start() \
        .Activate(views.one)

    one = flow.View(views.one) \
        .Next(views.two)

    two = flow.View(views.thee) \
        .Next(views.three)

    three = flow.View(views.three) \
        .Next(this.end)

    end = flow.End()
