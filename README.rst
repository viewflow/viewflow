===============
django-viewflow
===============

Ad-hoc business process automation framework for Django

django-viewflow provides simple, django friendly way to organize views, background jobs, user permission checking,
in one clearly defined task flow.

Quick start
===========
Here is the simple one task flow definition, put it in `flows.py` inside your django application::

    from viewflow import flow
    from viewflow.base import this, Flow
    from .views import hello_world_view

    class HelloWorldFlow(Flow):
        start = flow.Start().Activate(this.hello_world)
        hello_world = flow.View(hello_world_view).Next(this.end)
        end = flow.End()

And define simple function based view::

    from viewflow.flow import flow_view
    from .flows import HelloWorldFlow

    @flow_view()
    def hellow_world_view(request, activation):
        activation.prepare(request.POST or None)
        form = MyForm(instance=task.process, request.POST or None)

        if form.is_valid():
            form.save()
            activation.done()
            return redirect('viewflow:index', current_app=MyFlow.app_label)

       return render(request, templates, {'form': form, 'activation': activation},
                     current_app=HelloWorldFlow.namespace)

`Flow` class contains all url required for task processing::

    from django.conf.urls import patterns, url, include
    from .flows import HelloWorldFlow

    urlpatterns = patterns('',
        url(r'^', include(HelloWorldFlow.instance.urls)))
 
See more examples in `tests\\examples` directory

Change log
==========

0.1.0
-----

* Initial public prototype
* Basic set of tasks support (View, Job, If/Switch, Split/Join)
