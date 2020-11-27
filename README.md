# Viewflow


The Django extension for perfectionists with yesterday’s deadlines.

Viewflow is the reusable library eases to build business apps fast. Viewflow helps to organize people collaboration workflow, implement CRUD and reporting.

The goad of viewflow is to allow to get ready-to-use application on top of Django as fast as with no-code solution. But allow to gracefully replace built-in functionality part-by-part with your custom code. Viewflow has pre-buit UI, and assumes that you could implement your own.

[![travis-svg]][travis] [![requirements-svg]][requirements] [![pypi-version]][pypi] [![py-versions]][pypi]


Viewflow came in two flavors:
- Lightweight open-source library with only un-opinionated base functionality
  allows to build your own custom solution on top of it.
- PRO: Commercially supported reference implementation. Integrated with 3d-party
  django packages, allows to build ready-to-use apps with few lines of code.

<img src="assets/ShipmentProcess.png" alt="drawing" width="600"/>


## Installation

Viewflow works with Python 3.7 or greater, and Django 3.1+

Viewflow:

    pip install django-viewflow --pre

Viewflow-PRO

    pip install django-viewflow-pro  --extra-index-url https://pypi.viewflow.io/<licence_id>/simple/ --pre

## Quick start

You can get bare minimum pre-configured Django project with Viewflow enabled
with following command:

    npm init django project_name --viewflow

just replace "project_name"  with the desired name of your application module.

## Documentation

http://docs-next.viewflow.io/


## Demo

http://demo-next.viewflow.io/

## Cookbook

Samples applications code for Viewflow PRO available at:

http://cookbook.viewflow.io


## Components

### BPMN Workflow

`viewflow.workflow.*` is a lightweight workflow layer on top of Django's Model-View-Template that helps to organize people collaboration business logic.

<a href="https://demo-next.viewflow.io/helloworld/">
  <img src="assets/dashboard.png" alt="drawing" width="600"/>
</a>

Viewflow supports parallel activities, allows to have multiple active task at
the same time and synchronize people interactions with background python jobs.

```python
class HelloWorldFlow(flow.Flow):
    start = (
        flow.Start(
            views.CreateProcessView.as_view(
                fields=['text']
            )
        )
        .Permission(auto_create=True)
        .Next(this.approvement_split)
    )

    ...

urlpatterns = [
    path(
        'flow/',
        FlowAppViewset(
            HelloWorldFlow, icon=Icon('assignment')
        ).urls
    ),
    path('accounts/', AuthViewset().urls),
    path('', site.urls),
]
```
Quick start: https://docs-next.viewflow.io/bpmn/quick_start.html


### Class-based URL Configuration

A class with `.urls` property, suitable to include into `urlpatterns`

Same concept as Django's Class Based Views but for routing configuration.

Class based url configuration allows to provide configure existing built-in
application functionality, redefine part of views to your own.

Viewflow contains several pre-build url configurations to build a Site Menu
structure, CRUD functionality, quickly enable user interfaces for BPMN and FSM
Workflows, and many 3d party apps.

```python
from viewflow.contrib.auth import AuthViewset
from viewflow.urls import Application, Site, Viewset

class WebsiteViewset(Viewset):
    index_url = path('', index_view, name='index')

site = Site(title="ACME Corp", items=[
    Application(
        title='Sample App',
        icon=Icon('people'),
        app_name='emp',
        items=[
            WebsiteViewset(),
        ]
    ),
])

urlpatterns = [
    path('', site.urls),
    path('accounts/', AuthViewset(
        allow_password_change=True,
        with_profile_view=True
    ).urls),
]
```

See more at - https://docs-next.viewflow.io/frontend/viewset.html

### Finite State Machine

Finite state machine workflows is the declarative way to describe consecutive operation through set of states and transitions between them.

<a href="https://demo-next.viewflow.io/admin/review/review/">
  <img src="assets/fsm.png" alt="drawing" width="600"/>
</a>

`viewflow.fsm.*` can help you manage rules and restrictions around moving from one state to another. The package could be used to get low level db-independent fsm implementation, or to wrap existing database model, and implement simple persistent workflow process with quickly bootstrapped UI.

```python
from enum import Enum
from viewflow.fsm import State

class Stage(Enum):
   NEW = 1
   DONE = 2
   HIDDEN = 3


class MyFlow(object):
    stage = State(Stage, default=Stage.NEW)

    @stage.transition(source=Stage.NEW, target=Stage.DONE)
    def complete(self):
        pas

    @stage.transition(source=State.ANY, target=Stage.HIDDEN)
    def hide(self):
        pass

flow = NyFlow()
flow.stage == Stage.NEW  # True
flow.stage = Stage.DONE  # Raises AttributeError

flow.complete()
flow.stage == Stage.DONE  # True

flow.complete()  # Now raises TransitionNotAllowed
```

### JSON Storage for Django Models
Keep dumb business data, quick prototyping without DB migrations, replace multi-table inheritance with proxy models.

`viewflow.jsonstore.*` is the set of virtual Django Model fields that stores data inside single JSON database column.

```python
from viewflow import jsonstore
from django.db import models

class Employee(models.Model):
    data = JSONField(default={})
    full_name = jsonstore.CharField(max_length=250)
    hire_date = jsonstore.DateField()
```
The result model works like usual django model. All virtual fields are available to construct ModelForms, Viewsets and Admin interfaces.

```python
class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['full_name', 'hire_date', 'salary']

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'hire_date']
    fields = ['full_name', ('hire_date', 'salary')]
```
See more at: https://docs-next.viewflow.io/json_storage.html

### Material UI Kit

Viewflow provides theme kit based on Google Material Design components. Base templates, Login. Logout, Password management views, Forms and CRUD.

SPA look and fell with turbolinks enabled navigation and form processing.

All Javascript managed by WebComponnents based on Solid-JS library.

<p>
<a href="https://demo-next.viewflow.io/accounts/login/">
  <img src="assets/login.png" alt="drawing" width="193"/>
</a>
<a href="https://demo-next.viewflow.io/atlas/city/">
  <img src="assets/list.png" alt="drawing" width="200"/>
</a>
<a href="https://demo-next.viewflow.io/forms/bank/">
  <img src="assets/form.png" alt="drawing" width="220"/>
</a>
</p>

Documentation: https://docs-next.viewflow.io/frontend/index.html

### Reporting

TODO

## License

Viewflow is an Open Source project licensed under the terms of
the AGPL license - `The GNU Affero General Public License v3.0
<http://www.gnu.org/licenses/agpl-3.0.html>`_ with the Additional Permissions
described in `LICENSE_EXCEPTION <./LICENSE_EXCEPTION>`_

You can more read about AGPL at `AGPL FAQ <http://www.affero.org/oagf.html>`_
This package license scheme follows to GCC Runtime library licensing. If you use
Linux already, probably this package license, should not bring anything new to
your stack.

Viewflow PRO has a commercial-friendly license allowing private forks
and modifications of Viewflow. You can find the commercial license terms in COMM-LICENSE.


## Latest Changelog

### 2020-XX-XX

  * Work in progress


[travis-svg]: https://travis-ci.org/viewflow/viewflow.svg
[travis]: https://travis-ci.org/viewflow/viewflow
[pypi]: https://pypi.org/project/django-viewflow/
[pypi-version]: https://img.shields.io/pypi/v/django-viewflow.svg
[py-versions]: https://img.shields.io/pypi/pyversions/django-viewflow.svg
[requirements-svg]: https://requires.io/github/viewflow/viewflow/requirements.svg?branch=v2
[requirements]: https://requires.io/github/viewflow/viewflow/requirements/?branch=v2
