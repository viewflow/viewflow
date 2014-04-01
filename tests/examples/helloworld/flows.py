from viewflow import flow
from viewflow.base import this, Flow
from viewflow.views import TaskView
from viewflow.lock import select_for_update_lock

from examples.helloworld.models import HelloWorldProcess


class HelloWorldFlow(Flow):
    process_cls = HelloWorldProcess
    lock_impl = select_for_update_lock

    start = flow.Start() \
        .Activate(this.hello_request) \
        .Available(username='employee')

    hello_request = flow.View(TaskView.as_view(fields=['text'])) \
        .Next(this.approve)

    approve = flow.View(TaskView.as_view(fields=['approved'])) \
        .Permission('helloworld.can_approve_request') \
        .Next(this.end)

    end = flow.End()
