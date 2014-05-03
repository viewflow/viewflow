from viewflow import flow
from viewflow.base import this, Flow
from viewflow.views import StartView, ProcessView
from viewflow.lock import select_for_update_lock

from .models import HelloWorldProcess
from .tasks import send_hello_world_request


class HelloWorldFlow(Flow):
    process_cls = HelloWorldProcess
    lock_impl = select_for_update_lock

    start = flow.Start(StartView, fields=['text']) \
        .Permission('helloworld.can_start_process') \
        .Activate(this.approve)

    approve = flow.View(ProcessView, fields=['approved']) \
        .Permission('helloworld.can_approve_request') \
        .Next(this.send)

    check_approve = flow.If(cond=lambda p: p.approved) \
        .OnTrue(this.send) \
        .OnFalse(this.end)

    send = flow.Job(send_hello_world_request) \
        .Next(this.end)

    end = flow.End()
