===============
django-viewflow
===============

Reusable workflow library for Django http://viewflow.io.

Needle and thread to tie simple CRUD views and python functions in a complex business process.

Designed for:

* Back office automation
* People collaboration software
* Business process implementation

Features:

* Simple integration with django views/signals/models
* User and background tasks support
* Complex Split/Joins for parallel task execution
* Boilerplate urls registration and permission checks handling

Demo: http://examples.viewflow.io

.. image:: tests/examples/shipment/doc/ShipmentProcess.png
   :width: 400px

About hundred lines of code required to make this process `life
<tests/examples/shipment/>`_ with django-viewflow and django class
based views.

.. image:: https://travis-ci.org/viewflow/viewflow.svg
   :target: https://travis-ci.org/viewflow/viewflow

.. image:: https://requires.io/github/viewflow/viewflow/requirements.svg?branch=master
   :target: https://requires.io/github/viewflow/viewflow/requirements/?branch=master

.. image:: https://coveralls.io/repos/viewflow/viewflow/badge.png?branch=master
   :target: https://coveralls.io/r/viewflow/viewflow?branch=master

.. image:: https://badges.gitter.im/Join%20Chat.svg
   :alt: Join the chat at https://gitter.im/viewflow/viewflow
   :target: https://gitter.im/viewflow/viewflow?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge 


Installation
============

django-viewflow requires Python 3.3 or greater, django 1.6-1.8::

    pip install django-viewflow

For installing `Viewflow-Pro <http://viewflow.io/#viewflow_pro>`_ with Python 2.7 support::

    pip install django-viewflow-pro  --extra-index-url https://pypi.viewflow.io/<licence_id>/simple/

Or inside of your project by adding the following statement to requirements.txt::

    --extra-index-url https://pypi.viewflow.io/<licence_id>/

And add it into INSTALLED_APPS settings

.. code-block:: python

    INSTALLED_APPS = (
         ...
         'viewflow',
    )


Quick start
===========
See the introduction video_ or read below:

.. _video: http://vimeo.com/m/104701259

Let's define basic Hello Process where one could start hello world request, another person approves it,
and as soon as the request is approved it should be send into background.

Start with process database model definition

.. code-block:: python

    from django.db import models
    from viewflow.models import Process

    class HelloWorldProcess(Process):
        text = models.CharField(max_length=150)
        approved = models.BooleanField(default=False)

Define the actual task that says Hello to the World in `tasks.py`

.. code-block:: python

    import os

    from celery import shared_task
    from viewflow.flow import flow_job

    @shared_task()
    @flow_job()
    def send_hello_world_request(activation):
        with open(os.devnull, "w") as world:
            world.write(activation.process.text)


To make the above code work just put the following flow definition in `flows.py` module from your django application.

.. code-block:: python

    from viewflow import flow, lock
    from viewflow.base import this, Flow
    from viewflow.contrib import celery
    from viewflow.views import StartProcessView, ProcessView

    from . import models, tasks


    class HelloWorldFlow(Flow):
        process_cls = models.HelloWorldProcess
        lock_impl = lock.select_for_update_lock

        start = flow.Start(StartProcessView, fields=["text"]) \
            .Permission(auto_create=True) \
            .Next(this.approve)

        approve = flow.View(ProcessView, fields=["approved"]) \
            .Permission(auto_create=True) \
            .Next(this.check_approve)

        check_approve = flow.If(cond=lambda p: p.approved) \
            .OnTrue(this.send) \
            .OnFalse(this.end)

        send = celery.Job(tasks.send_hello_world_request) \
            .Next(this.end)

        end = flow.End()

`Flow` class contains all urls required for the task processing.

.. code-block:: python

    from django.conf.urls import patterns, url, include
    from viewflow import views as viewflow
    from .helloworld.flows import HelloWorldFlow

    urlpatterns = patterns('',
        url(r'^helloworld/', include([
            HelloWorldFlow.instance.urls,
            url('^$', viewflow.ProcessListView.as_view(), name='index'),
            url('^tasks/$', viewflow.TaskListView.as_view(), name='tasks'),
            url('^queue/$', viewflow.QueueListView.as_view(), name='queue'),
            url('^details/(?P<process_pk>\d+)/$', viewflow.ProcessDetailView.as_view(), name='details'),
        ], namespace=HelloWorldFlow.instance.namespace), {'flow_cls': HelloWorldFlow}))


Your Hello World process is ready to go. If you run the development server
locally, go to http://localhost:8000/helloworld/ and step through the workflow.


Next, you can see how to define custom views, and meet other concepts of django-viewflow at
http://kmmbvnr.github.io/django-viewflow/

More examples are available in the `tests/examples` directory.


License
=======
Viewflow is an Open Source project licensed under the terms of
the AGPL license - `The GNU Affero General Public License v3.0 <http://www.gnu.org/licenses/agpl-3.0.html>`_

Viewflow Pro has a commercial-friendly license allowing private forks
and modifications of Viewflow. You can find the commercial license terms in COMM-LICENSE.
Please see `FAQ <https://github.com/kmmbvnr/django-viewflow/wiki/Pro-FAQ>`_ for more detail.  


Latest changelog
================

0.9.0 - 2015-06-15
------------------

* Django 1.8 support
* Better inbox/queue views
* Improve undo/cancel tasks behaviour
* Allow to specify custom undo handlers methods
* Allow to use flow class methods as flow task functions
* Allow to list task state change handles in template
* *PRO ONLY* New Material Designed Frontend for the Flow

Roadmap
=======

* in 0.9.0 at January we going to extend documentation and improve task undo behaviour
* 1.0.0 LTS estimated at March 2015 would have lifetime support same as django 1.6
