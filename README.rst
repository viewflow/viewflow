===============
django-viewflow
===============

Ad-hoc business process automation framework for Django.

.. image:: https://travis-ci.org/kmmbvnr/django-viewflow.svg
   :target: https://travis-ci.org/kmmbvnr/django-viewflow

.. image:: https://requires.io/github/kmmbvnr/django-viewflow/requirements.png?branch=master
   :target: https://requires.io/github/kmmbvnr/django-viewflow/requirements/?branch=master

.. image:: https://coveralls.io/repos/kmmbvnr/django-viewflow/badge.png?branch=master
   :target: https://coveralls.io/r/kmmbvnr/django-viewflow?branch=master

The process logic defined with django-viewflow is concentrated in one clearly defined `flow`.
You can organize your views, background jobs, user permission checking in a simple, intuitive django-friendly way.

.. image:: tests/examples/shipment/doc/ShipmentProcess.png
   :width: 400px

django-viewflow allows to implement such process, just in about hundred lines of code, and you would still have pure django views for that.

Full documentation is available at http://kmmbvnr.github.io/django-viewflow/

Installation
============

django-viewflow requires Python 3.3 or greater and django 1.7::

    pip install django-viewflow

And add it into INSTALLED_APPS settings

.. code-block:: python

    INSTALLED_APPS = (
         ...
         viewflow,
    )


Quick start
===========
Let's define basic Hello Process where one could start hello world request, another person approves it,
and as soon as the request is approved it should be send into background.

Start with process database model definition

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

Define the actual task that says Hello to the World in `task.py`

.. code-block:: python

    import os

    from celery import shared_task
    from viewflow.flow import flow_job

    @shared_task(bind=True)
    @flow_job()
    def send_hello_world_request(self, activation):
        with open(os.devnull, "w") as world:
            world.write(activation.process.text)


To make the above code work just put the following flow definition in `flows.py` module from your django application.

.. code-block:: python

    from viewflow import flow, lock
    from viewflow.base import this, Flow
    from viewflow.views import ProcessView
    from .models import HelloWorldProcess

    class HelloWorldFlow(Flow):
        process_cls = HelloWorldProcess
        lock_impl = lock.select_for_update_lock

        start = flow.Start(StartView, fields=["text"]) \
           .Permission('helloworld.can_start_request') \
           .Next(this.hello_world)

        approve = flow.View(ProcessView, fields=["approve"]) \
            .Permission('helloworld.can_approve_request')
            .Next(this.check_approve)

        check_approve = flow.If(cond=lambda p: p.approved) \
            .OnTrue(this.send) \
            .OnFalse(this.end)

        send = flow.Job(send_hello_world_request) \
            .Next(this.end)

        end = flow.End()

`Flow` class contains all urls required for the task processing.

.. code-block:: python

    from django.conf.urls import patterns, url, include
    from .flows import HelloWorldFlow

    urlpatterns = patterns('',
        url(r'^helloworld/', include(HelloWorldFlow.instance.urls)))


That's all you need to setup this flow.

Next, you can see how to define custom views, and meet other concepts of django-viewflow at
http://kmmbvnr.github.io/django-viewflow/

More examples are available in the `tests/examples` directory.


License
=======
`The GNU Affero General Public License v3.0 <https://www.gnu.org/copyleft/gpl.html>`_

Changelog
=========

0.3.0 2014-07-01
-----------------

* Added auto create task permission shortcuts
* Allow to provide process and task description in docstrings
* Started bootstrap based viewflow base site interface
* Bootstrap based custom form redefinable form rendering
* django-extra-views friendly views mixins
* Fix start task owner assigenment
* Task done redirect now points to next flow assigned task if exists
* Flow Start.Activate renamed to .Next in order to be same as flow.View interface


0.2.0 2014-06-02
----------------

* Back reference for task owner for next tasks assignment
* Auto create for task permissions support
* Basic django admin interace
* Exception handling during flow task activation and for broken celery jobs


0.1.0  2014-05-01
-----------------

* Initial public prototype
* Basic set of tasks support (View, Job, If/Switch, Split/Join)
