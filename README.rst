===============
django-viewflow
===============

Ad-hoc business process automation framework for Django

django-viewflow provides simple, django friendly way to organize views, background jobs, user permission checking,
in one clearly defined task flow.

django-viewflow allows to implement such process, just in about hundred lines of code, and still have pure django views for that

.. image:: tests/examples/shipment/doc/ShipmentProcess.png
   :align: right
   :width: 400px
     
Installation
============

django-viewflow requires Python 3.3 or grater and django 1.7::

    pip install django-viewflow

And add it into INSTALLED_APPS settings

.. code-block:: python

    INSTALLED_APPS = (
         ...
         viewflow,
    )


Quick start
===========
Let's define basic Hello Process where one could start hello world request, another approve it,
and when request approved, it should be send in background.

Start with process model definition

.. code-block:: python

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

Define the actual task that would perform Hello on World, in task.py

.. code-block:: python

    import os

    from celery import shared_task
    from viewflow.flow import flow_job

    @shared_task(bind=True)
    @flow_job()
    def send_hello_world_request(self, activation):
        with open(os.devnull, "w") as world:
            world.write(activation.process.text)


To make this code works flow definition is simple, put it in `flows.py` inside your django application

.. code-block:: python

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

`Flow` class contains all url required for task processing

.. code-block:: python

    from django.conf.urls import patterns, url, include
    from .flows import HelloWorldFlow

    urlpatterns = patterns('',
        url(r'^helloworld/', include(HelloWorldFlow.instance.urls)))


That's all you need to setup this flow.

Next, you can see how to define custom views `TODO` meet with and other concepts `TODO` of django-viewflow

More examples available in `tests\\examples` directory


License
======
`The GNU General Public License v3.0 <https://www.gnu.org/copyleft/gpl.html>`_

Change log
==========

0.1.0
-----

* Initial public prototype
* Basic set of tasks support (View, Job, If/Switch, Split/Join)
