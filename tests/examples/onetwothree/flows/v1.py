from viewflow import flow
from viewflow.base import this, Flow
from viewflow.views import TaskView

from examples.onetwothree.models import HelloWorldProcess


class HelloWorldFlow(Flow):
    process_cls = HelloWorldProcess

    start = flow.Start() \
        .Activate(this.hello_request)

    hello_request = flow.View(TaskView.as_view(fields=['text'])) \
        .Next(this.approve)

    approve = flow.View(TaskView.as_view(fields=['approved'])) \
        .Permission('onetwothree.can_approve_request') \
        .Next(this.end)

    end = flow.End()
