===============
django-viewflow
===============

Ad-hoc business process automation framework for Django http://viewflow.io.

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

django-viewflow requires Python 3.3 or greater, django 1.6::

    pip install django-viewflow

For installing viewflow-pro with Python 2.7 support::

    pip install mock django-viewflow  --extra-index-url http://<your_id>.pypi.viewflow.io/

Or inside of your project by adding the following statement to requirements.txt::

    --extra-index-url http://<your_id>.pypi.viewflow.io/

And add it into INSTALLED_APPS settings

.. code-block:: python

    INSTALLED_APPS = (
         ...
         'viewflow',
         'viewflow.site',
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
    from viewflow.views import StartView, ProcessView
    from viewflow.site import viewsite

    from . import models, tasks


    class HelloWorldFlow(Flow):
        process_cls = models.HelloWorldProcess
        lock_impl = lock.select_for_update_lock

        start = flow.Start(StartView, fields=["text"]) \
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


    viewsite.register(HelloWorldFlow)

`Flow` class contains all urls required for the task processing.

.. code-block:: python

    from django.conf.urls import patterns, url, include
    from viewflow.site import viewsite

    urlpatterns = patterns('',
        url(r'^flows/', include(viewsite.urls)))


Your Hello World process is ready to go. If you run the development server
locally, go to http://localhost:8000/flows/helloworld/ and step through the workflow.


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

Changelog
=========

0.6.0 2014-10-01
----------------

* First beta version. First public available release with commercial support and licencing.
* All API that could be imported as `from viewflow.some_package import cls_or_function` considered stable and
  not going to be changed much till 1.0 release (except `viewflow.site` that's still under develpment)
* Django 1.6 support available in public version of viewflow library
* Added task details views
* Custom tag creation simplified
* Split flow base classes to be independed from Django permission system
* Object level permission support for tasks.
* Improved {% flowurl %} tag
* {% flow_perms %} tag for task permission list in template
* Base abstract classes for models
* New video: Viewflow Internals - https://vimeo.com/107698021


0.5.0 2014-09-01
----------------

* Many improvements on viewsite
    - Explicit flow registration on viewsite
    - Process details, task and queus views
    - Permission base filtering
* New example: custom flow node and dynamic splitting
* Celery dependecy optional and moved to contrib package
* Examples available live at http://examples.viewflow.io
* Started introduction video series - https://vimeo.com/104701259

0.4.0 2014-08-01
-----------------

* Demo and promo available at http://viewflow.io
* Introduced django signals, python functions as flow task
* Improved form rendering, dynamic formset support out of the box
* Refactor viewflow.site to separate app


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


Roadmap
=======

* 0.5.0 going to be the last alpha release
* 0.6.0 at 1st October would have considered first beta release with stable API
* 1.0.0 LTS estimated at January/February 2015 would have lifetime support same as django 1.6
