# Viewflow

**The low-code for developers with yesterday's deadline**

[![build]][build] [![coverage]][coverage] [![pypi-version]][pypi] [![py-versions]][pypi]

Viewflow is a reusable component library for building business applications with
ease. It's built on top of Django, making it accessible for developers with
experience in these technologies. With Viewflow, you can create full-featured
business applications in just a few lines of code using its reusable component
library.

Like Django, Viewflow shipped as a single package with batteries included. Each
part Viewflow can be used independently of each other, but they all work well
together.

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

    pip install django-viewflow --pre

Viewflow-PRO

    pip install django-viewflow-pro  --extra-index-url https://pypi.viewflow.io/<licence_id>/simple/ --pre

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
        tips_received = json_Store.IntegerField(default=0)

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

    from viewflow.contrib.auth import AuthViewset
    from viewflow.urls import Application, Site
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

4. Run migrations and access the workflow through the pre-built frontend.

Run migrations to create the necessary database tables, then start your Django
server and access the workflow through the pre-built frontend. You should be
able to create and track pizza orders with the workflow.

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

Viewflow is an Open Source project licensed under the terms of
the AGPL license - `The GNU Affero General Public License v3.0
<http://www.gnu.org/licenses/agpl-3.0.html>`_ with the Additional Permissions
described in `LICENSE_EXCEPTION <./LICENSE_EXCEPTION>`_

You can read more about AGPL at `AGPL FAQ <http://www.affero.org/oagf.html>`_
This package license scheme follow GCC Runtime library licensing. If you use Linux already, this package license likely won't bring anything new to your stack.

Viewflow PRO has a commercial-friendly license allowing private forks
and modifications of Viewflow. You can find the commercial license terms in COMM-LICENSE.


## Changelog

2.0.0.b2 2023-03-06
-------------------

- Revised and improved documentation https://docs-next.viewflow.io
- Extend autocomplete mixins for the formtools wizard support
- Add support for list_paginate_by count to the model viewset
- Virtual json fields got support in .values() and .values_list() queryset
- Add missing .js.map static files

[build]: https://img.shields.io/github/actions/workflow/status/viewflow/viewflow/django.yml?branch=main
[coverage]: https://img.shields.io/coveralls/github/viewflow/viewflow/v2
[travis-svg]: https://travis-ci.org/viewflow/viewflow.svg
[travis]: https://travis-ci.org/viewflow/viewflow
[pypi]: https://pypi.org/project/django-viewflow/
[pypi-version]: https://img.shields.io/pypi/v/django-viewflow.svg
[py-versions]: https://img.shields.io/pypi/pyversions/django-viewflow.svg
[requirements-svg]: https://requires.io/github/viewflow/viewflow/requirements.svg?branch=v2
[requirements]: https://requires.io/github/viewflow/viewflow/requirements/?branch=v2
