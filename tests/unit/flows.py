from django.contrib.auth.models import User

from viewflow import flow
from viewflow.base import Flow, this

from unit.models import TestProcess


def perform_task(request, act_id):
    raise NotImplementedError


class SingleTaskFlow(Flow):
    start = flow.Start() \
        .Activate('task')
    task = flow.View(perform_task)\
        .Next('end')
    end = flow.End()


class AllTaskFlow(Flow):
    start = flow.Start().Activate(this.view)
    view = flow.View().Next(this.job)
    job = flow.Job(lambda act_id: None).Next(this.iff)
    iff = flow.If(lambda act: True).OnTrue(this.switch).OnFalse(this.switch)
    switch = flow.Switch().Default(this.split)
    split = flow.Split().Always(this.join)
    join = flow.Join().Next(this.first)
    first = flow.First().Of(this.timer)
    timer = flow.Timer().Next(this.mailbox)
    mailbox = flow.Mailbox(lambda a: None).Next(this.end)
    end = flow.End()


class RestrictedUserFlow(Flow):
    start = flow.Start().Activate(this.view)
    view = flow.View().Next(this.end).Assign(username='employee')
    end = flow.End()


class RestrictedCallableUserFlow(Flow):
    start = flow.Start().Activate(this.view)
    view = flow.View().Next(this.end).Assign(lambda p: User.objects.get(username='employee'))
    end = flow.End()


class RestrictedPermissionFlow(Flow):
    process_cls = TestProcess

    start = flow.Start().Activate(this.view)
    view = flow.View().Next(this.end).Permission('unit.restricted_permission_flow__view')
    end = flow.End()
