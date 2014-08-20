from viewflow import flow, lock, views as flow_views
from viewflow.base import this, Flow
from viewflow.site import viewsite


from .models import HelloWorldProcess
from .tasks import send_hello_world_request


class HelloWorldFlow(Flow):
    """
    Hello world

    This process demonstrates hello world approval request flow.

    1. User with *helloworld.can_start_process* permission creates hello world request
    2. Manager, who have *helloworld.can_approve_request* approves it
    3. And if request was approved, background celery job sends it to the world
    4. Elsewhere, request became cancelled
    """
    process_cls = HelloWorldProcess
    lock_impl = lock.select_for_update_lock

    start = flow.Start(flow_views.StartProcessView, fields=['text']) \
        .Permission(auto_create=True) \
        .Next(this.approve)

    approve = flow.View(flow_views.ProcessView, fields=['approved']) \
        .Permission(auto_create=True) \
        .Next(this.send)

    check_approve = flow.If(cond=lambda p: p.approved) \
        .OnTrue(this.send) \
        .OnFalse(this.end)

    send = flow.Job(send_hello_world_request) \
        .Next(this.end)

    end = flow.End()


viewsite.register(HelloWorldFlow)
