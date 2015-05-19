from viewflow import flow, lock, views as flow_views
from viewflow.base import this, Flow
from viewflow.contrib import celery


from .models import HelloWorldProcess
from .tasks import send_hello_world_request


class HelloWorldFlow(Flow):
    """
    Hello world

    This process demonstrates hello world approval request flow.
    """
    process_cls = HelloWorldProcess
    lock_impl = lock.select_for_update_lock

    summary_template = "'{{ process.text }}' message to the world"
    
    start = flow.Start(flow_views.StartProcessView, fields=['text']) \
        .Permission(auto_create=True) \
        .Next(this.approve)

    approve = flow.View(flow_views.ProcessView, fields=['approved'],
                        task_description="Message approvement required",
                        task_result_summary="Messsage was {{ process.approved|yesno:'Approved,Rejected' }}") \
        .Permission(auto_create=True) \
        .Next(this.check_approve)

    check_approve = flow.If(cond=lambda p: p.approved) \
        .OnTrue(this.send) \
        .OnFalse(this.end)

    send = celery.Job(send_hello_world_request) \
        .Next(this.end)

    end = flow.End()
