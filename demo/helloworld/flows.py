import os
from django.utils.translation import ugettext_lazy as _

from viewflow import flow, frontend, lock
from viewflow.base import this, Flow
from viewflow.flow import views as flow_views


from .models import HelloWorldProcess


@frontend.register
class HelloWorldFlow(Flow):
    """
    Hello world

    This process demonstrates hello world approval request flow.
    """
    process_class = HelloWorldProcess
    process_title = _('Hello world')
    process_description = _('This process demonstrates hello world approval request flow.')

    lock_impl = lock.select_for_update_lock

    summary_template = _("'{{ process.text }}' message to the world")

    start = (
        flow.Start(
            flow_views.CreateProcessView,
            fields=['text'],
            task_title=_('New message'))
        .Permission(auto_create=True)
        .Next(this.approve)
    )

    approve = (
        flow.View(
            flow_views.UpdateProcessView, fields=['approved'],
            task_title=_('Approve'),
            task_description=_("{{ process.text }} approvement required"),
            task_result_summary=_("Messsage was {{ process.approved|yesno:'Approved,Rejected' }}"))
        .Permission(auto_create=True)
        .Next(this.check_approve)
    )

    check_approve = (
        flow.If(
            cond=lambda act: act.process.approved,
            task_title=_('Approvement check'),
        )
        .Then(this.send)
        .Else(this.end)
    )

    send = (
        flow.Handler(
            this.send_hello_world_request,
            task_title=_('Send message'),
        )
        .Next(this.end)
    )

    end = flow.End(
        task_title=_('End'),
    )

    def send_hello_world_request(self, activation):
        with open(os.devnull, "w") as world:
            world.write(activation.process.text)
