from viewflow import flow
from viewflow.base import this, Flow
from viewflow.views import TaskView

from examples.helloworld.models import HelloWorldProcess


class HelloWorldFlow(Flow):
    process_cls = HelloWorldProcess

    start = flow.Start() \
        .Activate(this.hello_request)

    hello_request = flow.View(TaskView.as_view(fields=['text'])) \
        .Next(this.approve)

    approve = flow.View(TaskView.as_view(fields=['approved'])) \
        .Permission('helloworld.can_approve_request') \
        .Next(this.end)

    end = flow.End()
