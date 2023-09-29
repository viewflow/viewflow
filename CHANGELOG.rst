=========
Changelog
=========

2.0.0.b8 2023-09-29
-------------------

- Fixed default values for jsonstore fields in forms.
- Pre-built workflow views now accept the layout option for forms.
- Improved success redirects for workflow action views.
- Enabled the 'Undo' action for celery.Job.
- Extended celery.Job activation to allow its use within the start and end tasks of celery.chord.
- Stored error traces and local variables in task.data JSON for failed celery.Job tasks.
- Enhanced handling of obsolete nodes.
- Fixed the JS calendar date shift issue for time zones with negative time offsets.


2.0.0.b7 2023-08-25
-------------------

- Fix pre-populated file field value
- Improvements for depended select widget
- Add total  counter widget
- Improve wizard template default breadcrumbs
- Support for %b date format

2.0.0.b6 2023-07-28
-------------------

- Fix label for File and Image fields

2.0.0.b5 2023-07-10
-------------------

- Alow attach layout to forms in default form rendering template
- Fix subprocess node activation
- Added db indexes for workflow models
- Improve workflow REST API support

2.0.0.b4 2023-06-05
-------------------

- New flow.SplitFirst Node
- New celery.Timer Node
- Expose REST API with drf-spectacular
- Expose list_ordering_fields in a ModelViewset
- Retain history and return to the Inbox/Queue list views after completing a flow task
- Enable smooth page transitions in Chrome/Safari
- Hotwire/Turbo integration for Django Admin with viewflow.contrib.admin app
- Resolved issue with viewflow.fsm reporting unmet condition messages

2.0.0.b3 2023-04-25
-------------------

- Fix migrations to BigAutoField
- Reintroduce workflow task signals


2.0.0.b2 2023-03-06
-------------------

- Revised and improved documentation https://docs.viewflow.io
- Extend autocomplete mixins for the formtools wizard support
- Add support for list_paginate_by count to the model viewset
- Virtual json fields got support in .values() and .values_list() queryset
- Add missing .js.map static files

2.0.0b1 2023-01-23
------------------
- Combined with django-material/django-fsm/jsonstore as a single package
- Switched to Google Material Components instead of MaterializeCSS
- Switched to hotwire/turbo instead of Turbolinks
- New Class-based URL configurations
- Composite FK support for legacy database for Django ORM
- Plotly dashboards integration
- Improved order of subsequent workflow tasks activations
- Many more improvements and fixes

1.11.0 2021-04-05
-----------------

- Django 4.0 fixes
- Simplify frontend task model customization


1.10.1 2021-12-10
-----------------

- Django 4.0 fixes


1.10.0 2021-11-12
-----------------

- Django 4.0 support
- Fix set assigned time on auto-assign
- Allow anonymous users to trigger flow start


1.9.0 2021-04-30
----------------

- Add additional template blocks for left panel. Close #311
- Fix issue with task assign on default POST
- Fix Spanish translation
- Add Italian translation
- Add custom rollback to update_status migration


1.8.1 2021-01-15
----------------

* Fix this-references for flow.Function task loader


1.8.0 2021-01-07
----------------

* Clean Django 4.0 warnings
* Allow flow.Handler redefinition with inheritance


1.7.0 2020-11-18
----------------

* Fix TaskQuerySet.user_queue filtering. Remove django 1.8 compatibility code


1.6.1 2020-05-13
----------------

* Fix auto permission creation for flow.View nodes
* Make django-rest-swagger requirements optional
* Fix REST Charts on python 3+


1.6.0 2019-11-19
----------------

* Django 3.0 support
* Add process.artifact and task.artifact generic fk fields for default models
* Add process.data and task.data generic json field for default models
* Add View().OnCreate(...) callback support
* Allow to override flow view access by Flow.has_view_permission method


1.5.3 2019-04-23
----------------

* Resolve this-references for Split and Switch nodes conditions


1.5.1 2019-02-25
----------------

* Task description field became rendered as django template with {{ process }} and {{ task }} variable available


1.5.0 2019-02-13
----------------

* Added portuguese translation


1.4.0 2018-10-25
----------------

* WebComponent based frontend (compatibility with django-material 1.4.x)
* Django 2.1 support
* [PRO] Flow chart internationalization


1.3.0 2018-08-23
----------------

* Django 2.1 support
* Support task permission checks on user model subclasses
* [PRO] django-rest-swagger 2.2.0 support


1.2.5 2018-05-07
----------------

* Fix process description translation on django 2.0
* Fix process dump data on django 2.0
* [PRO] Frontend - fix page scroll on graph model open


1.2.2 2018-02-26
----------------

* Fix admin actions menu
* Fix this-reference usage in If-node condition.
* [PRO] Expose Celery Retry task action
* [PRO] Fix obsolete node url resolve

1.2.0 2017-12-20
----------------

* Django 2.0 support
* Drop compatibility with Django 1.8/1.9/1.10
* Materialize 1.0.0 support

1.1.0 2017-11-01
----------------
* Fix prefetch_related usage on process and task queryset
* Fix runtime error in python2.7/gunicorn deployment
* [PRO] REST API support

1.0.0 2017-05-29
----------------

* Django 1.11 support
* Open-sourced Python 2.7 support
* Added AGPL license additional permissions (allows to link with commercial software)
* Localization added: German/French/Spanish/Korean/Chinese
* Improved task detail UI in frontend
* Frontend - task management menu fix
* `JobActivation.async` method renamed to `run_async`. Fix python 3.7 reserved word warning.
* [PRO] New process dashboard view
* [PRO] Django-Guardian support for task object level permissions
* [PRO] Fixes and improvements in the flow chart rendering


0.12.0 - 2017-02-14
-------------------

This is the cumulative release with many backward incompatibility changes.

* Django 1.6 now longer supported.

* Frontend now a part of the open-source package.

* Flow chart visualization added

* Every _cls suffix, ex in flow_cls, activation_cls, was renamed to
  _class. The reason for that is just to be consistent with django
  naming theme.

* Django-Extra-Views integration is removed. This was a pretty creepy
  way to handle Formsets and Inlines within django class-based
  views. Instead, django-material introduce a new way to handle Form
  Inlines same as a standard form field. See details in the
  documentation.

* Views are no longer inherits and implement an Activation
  interface. This change makes things much simple internally, and
  fixes inconsistency, in different scenarios. @flow_view,
  @flow_start_view decorators are no longer callable.

* Activation now passed as a request attribute. You need to remove
  explicit activation parameter from view function signature, and use
  request.activation instead. 

* Built-in class based views are renamed, to be more consistent. Check
  the documentation to find a new view name.

* If().OnTrue().OnFalse() renamed to If().Then().Else()

* All conditions in If, Switch and other nodes receives now a node
  activation instance instead of process. So you can gen an access to
  the current task via activation.task variable.

* Same for callable in the .Assign() and .Permissions definitions.

* task_loader not is the attribute of a flow task. In makes functions
  and signal handlers reusable over different flows.

* Flow namespace are no longer hard-coded. Flow views now can be
  attached to any namespace in a URL config. 

* flow_start_func, flow_start_signal decorators need to be used for
  the start nodes handlers. Decorators would establish a proper
  locking avoids concurrent flow process modifications in the
  background tasks.

* To use celery job with django 1.8, django-transaction-hooks need to
  be enabled.
