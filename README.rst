===============
django-viewflow
===============

Ad-hoc business process automation framework for Django

django-viewflow provides simple, django friendly way to organize views, background jobs, user permission checking,
in one clearly defined task flow.

django-viewflow does not introduce any restriction on views, urls or celery tasks, and should plays well
in any other django project.


Quick start
===========
Let's define basic Hello Process where one could start hello world request, and another approve it,
when request approved, it should be send.

Start with process model definition::

    from django.db import models
    from viewflow.models import Process

    class HelloworldProcess(Process):
        text = models.ChatField(max_lenght=150, blank=True, null=True)
        approved = models.BooleanField(default=False)

        class Meta:
            permissions = [
                ('can_start_request', 'Can start hello world request'),
                ('can_approve_request', 'Can approve hello world request')
            ]

Define the actual task that would perform Hello on World, in task.py::

    import os

    from celery import shared_task
    from viewflow.flow import flow_job

    @shared_task(bind=True)
    @flow_job()
    def send_hello_world_request(self, activation):
        with open(os.devnull, "w") as world:
            world.write(activation.process.text)


To make this code works flow definition is simple, put it in `flows.py` inside your django application::

    from viewflow import flow
    from viewflow.base import this, Flow
    from viewflow.views import ProcessView

    class HelloWorldFlow(Flow):
        start = flow.Start(StartView, fields=["text"]) \
           .Permission('helloworld.can_start_request') \
           .Activate(this.hello_world)

        approve = flow.View(ProcessView, fields=["approve"]) \
            .Permission('helloworld.can_approve_request')
            .Next(this.check_approve)

        check_approve = flow.If(cond=lambda p: p.approved) \
            .OnTrue(this.send) \
            .OnFalse(this.end)

        send = flow.Job(send_hello_world_request) \
            .Next(this.end)

        end = flow.End()

`Flow` class contains all url required for task processing::

    from django.conf.urls import patterns, url, include
    from .flows import HelloWorldFlow

    urlpatterns = patterns('',
        url(r'^helloworld/', include(HelloWorldFlow.instance.urls)))


That's all you need to setup this flow.

Next, you can see how to define custom views `TODO` meet with and other concepts `TODO` of django-viewflow

More examples available in `tests\\examples` directory

Change log
==========

0.1.0
-----

* Initial public prototype
* Basic set of tasks support (View, Job, If/Switch, Split/Join)
