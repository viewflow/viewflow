# Viewflow

**The low-code for developers with yesterday's deadline**

[![build]][build] [![coverage]][coverage] [![pypi-version]][pypi] [![py-versions]][pypi]


Viewflow is a low-code, reusable component library for creating comprehensive business applications with ease. Built on top of Django, Viewflow simplifies development by providing pre-built components for user management, workflows, and reporting, while still offering flexibility to customize and integrate with existing systems.

With Viewflow, you can create full-featured business applications in just a few lines of code using its reusable component library. It's shipped as a single package with batteries included, and each part of Viewflow can be used independently of the others, but they all work well together.


Viewflow comes in two flavors:
- **Viewflow Core:** A lightweight, open-source library with only non-opinionated core classes that allows you to build your custom solution on top.
- **Viewflow PRO:** A comprehensive package that includes reference functionality implementation and integrated with third-party Django packages. This package has a commercial-friendly license that allows private forks and modifications of Viewflow.

<img src="assets/ShipmentProcess.png" alt="drawing" width="600"/>

## Features

- Modern, responsive user interface with an SPA-style look and feel
- Reusable workflow library for quick implementation of BPMN workflows
- Built-in customizable CRUD for managing complex forms and data
- Integrated reporting dashboard
- Small and concise API


## Installation

Viewflow works with Python 3.8 or greater and Django 4.0+

Viewflow:

    pip install django-viewflow

Viewflow-PRO:

    pip install django-viewflow-pro  --extra-index-url https://pypi.viewflow.io/<licence_id>/simple/

Add 'viewflow' and, in case you need workflow capabilities 'viewflow.workflow' to the INSTALLED_APPS settings.py

```python
    INSTALLED_APPS = [
        ....
        'viewflow',
        'viewflow.workflow',
    ]
```


## Quick start

Here's an example of how to create a simple pizza ordering workflow using Viewflow:

1. Create a model to store process data

Before creating the workflow, you'll need to define a model to store the process
data. Viewflow provides a Process model as the base model for your process
instances. You can add your own fields to the model using jsonstore fields to
avoid model inheritance and additional joins:

```python

    from viewflow import jsonstore
    from viewflow.workflow.models import Process

    class PizzaOrder(Process):
        customer_name = jsonstore.CharField(max_length=250)
        address = jsonstore.TextField()
        toppings = jsonstore.TextField()
        tips_received = jsonstore.IntegerField(default=0)
        baking_time = jsonstore.IntegerField(default=10)

        class Meta:
            proxy = True
```

2. Create a new flow definition file flows.py

Next, create a new flow definition file *flows.py* and define your workflow. In
this example, we'll create a PizzaFlow class that inherits from flow.Flow.
We'll define three steps in the workflow: start, bake, and deliver. We'll
use CreateProcessView and UpdateProcessView to create and update the process
data from PizzaOrder:

```python

    from viewflow import this
    from viewflow.workflow import flow
    from viewflow.workflow.flow.views import CreateProcessView, UpdateProcessView
    from .models import PizzaOrder

    class PizzaFlow(flow.Flow):
        process_class = PizzaOrder

        start = flow.Start(
            CreateProcessView.as_view(
                fields=["customer_name", "address", "toppings"]
            )
        ).Next(this.bake)

        bake = flow.View(
            UpdateProcessView.as_view(fields=["baking_time"])
        ).Next(this.deliver)

        deliver = flow.View(
            UpdateProcessView.as_view(fields=["tips_received"])
        ).Next(this.end)

        end = flow.End()
```

3. Add the flow to your URL configuration:

Finally, add the PizzaFlow to your URL configuration. You can use the Site and
FlowAppViewset classes to register your workflow with the pre-built frontend.

```python

    from django.urls import path
    from viewflow.contrib.auth import AuthViewset
    from viewflow.urls import Application, Site
    from viewflow.workflow.flow import FlowAppViewset
    from my_pizza.flows import PizzaFlow

    site = Site(
        title="Pizza Flow Demo",
        viewsets=[
            FlowAppViewset(PizzaFlow, icon="local_pizza"),
        ]
    )

    urlpatterns = [
        path("accounts/", AuthViewset().urls),
        path("", site.urls),
    ]

```

4. Make and run migrations and access the workflow through the pre-built frontend.

Make and run migrations to create the necessary database tables, then start your Django
server and access the workflow through the pre-built frontend. You should be
able to create and track pizza orders with the workflow.

Go to the https://docs.viewflow.io/workflow/writing.html for the next steps

## Documentation

Viewflow's documentation for the latest version is available at
http://docs.viewflow.io/

Documentarian for Viewflow  1.xx  series available at http://v1-docs.viewflow.io


## Demo

http://demo.viewflow.io/

## Cookbook

For sample applications and code snippets, check out the Viewflow PRO cookbook at

https://github.com/viewflow/cookbook


## License

Viewflow is an Open Source project licensed under the terms of the AGPL license - [The GNU Affero General Public License v3.0](http://www.gnu.org/licenses/agpl-3.0.html) with the Additional Permissions
described in [LICENSE_EXCEPTION](./LICENSE_EXCEPTION)

The AGPL license with Additional Permissions is a free software license that
allows commercial use and distribution of the software. It is similar to the GNU
GCC Runtime Library license, and it includes additional permissions that make it
more friendly for commercial development.

You can read more about AGPL and its compatibility with commercial use at the
[AGPL FAQ](http://www.affero.org/oagf.html)

If you use Linux already, this package license likely won't bring anything new to your stack.

Viewflow PRO has a commercial-friendly license allowing private forks and
modifications of Viewflow. You can find the commercial license terms in
[COMM-LICENSE](./COMM-LICENSE).

## Changelog

### 2.1.2 2024-06-24

- Allow cancelling Celery tasks from the ERROR state.
- Hotfix: Fix broken Join when no other nodes are created by Split.
- Allow using this references to flow static methods as Celery tasks.
- Allow cancelling Celery jobs from the ERROR status.
- Add missing permission check before adding a new item to the list.
- Allow Admin() viewset to be used as a sub-item in an Application viewset.

### 2.1.1 2024-06-06

- Hotfix broken task creation


### 2.1.0 2024-06-16

- Allow to assign additional custom data to viewflow.fsm transitions
- Added `data_source` parameter to `Split.Next()` method, allowing dynamic creation of multiple node instances based on a list of data items.


[build]: https://img.shields.io/github/actions/workflow/status/viewflow/viewflow/django.yml?branch=main
[coverage]: https://img.shields.io/coveralls/github/viewflow/viewflow/v2
[travis-svg]: https://travis-ci.org/viewflow/viewflow.svg
[travis]: https://travis-ci.org/viewflow/viewflow
[pypi]: https://pypi.org/project/django-viewflow/
[pypi-version]: https://img.shields.io/pypi/v/django-viewflow.svg
[py-versions]: https://img.shields.io/pypi/pyversions/django-viewflow.svg
[requirements-svg]: https://requires.io/github/viewflow/viewflow/requirements.svg?branch=v2
[requirements]: https://requires.io/github/viewflow/viewflow/requirements/?branch=v2
