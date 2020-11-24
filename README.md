# Viewflow

The Django extension for perfectionists with yesterday’s deadlines.

Viewflow is the reusable library eases to build business apps fast. Viewflow
helps to organize people collaboration workflow, implement CRUD and reporting.

The goad of viewflow is to allow to get ready-to-use application on top of
Django as fast as with no-code solution. But allow gracefully replace built-in
functionality part-by-part with your custom code.

Viewflow came in two flavors:
- Lightweight BSD-licensed library with only un-opinionated base functionality
  allows to build your own custom solution on top of it.
- PRO: Commercially supported reference implementation. Integrated with 3d-party
  django packages, allows to build ready-to-use apps with few lines of code.

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

Viewflow supports parallel activities, allows to have multiple active task at
one and synchronize people interactions with background python jobs.

Quick start: https://docs-next.viewflow.io/bpmn/quick_start.html

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

```

### Class-based URL Configuration

TODO

### Deployment automation

    $ npm init django

### Finite State Machine

Sequential

TODO

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

### Material UI Kit

TODO

### Reporting

TODO


## Latest Changelog

### 2020-XX-XX

  * Work in progress
