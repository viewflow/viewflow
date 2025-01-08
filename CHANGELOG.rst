=========
Changelog
=========

2.2.9 2025-01-08
----------------

- Enhanced validation for flow_refs and task_refs to ensure accuracy and consistency.
- Resolved an issue with canceling processes containing revived tasks.
- Corrected the password reset confirmation email template for better functionality.
- Fixed multipart form type detection for forms with file fields in formsets.


2.2.8 2024-10-04
----------------

- Prevent exceptions from being raised by Process/Task models when a flow class
  is deleted but still referenced in the database.
- Fix serialization issue with jsonstore.DecimalField.
- Add missing 'index' view for celery.Task node.
- Enable recovery of flow.Subprocess and flow.NSubprocess nodes from error state.
- Correct invalid typing for FSM conditions.
- Allow setting permission=None in the FSM @transition decorator to explicitly bypass permission checks.
- Add support for MultiValueField and django-money fields form rendering

2.2.7 2024-08-16
----------------

- Added compatibility fix for Python 3.8.
- Extend documentation with data management explanation - https://docs.viewflow.io/workflow/data_flow.html
- Expanded documentation to cover permission management - https://docs.viewflow.io/workflow/permissions.html
- Introduced an experimental JSONEditorWidget.
- Fixed issue with saving the state of revived tasks.
- Enabled the option to cancel If tasks.
- Updated default FSM state change in FlowViewsMixin to now use transaction.atomic.
- Added support for using DependentModelSelect in formsets.
- Enabled AjaxModelSelect to function as a dependency for DependentModelSelect
- Corrected typo in the deletion success message.
- Test under django 5.1

2.2.6 2024-08-04
----------------

- Resolved the flow.If condition's this reference during class construction.
- Improved error handling when a Celery task finishes.
- Fixed an issue where errors occurring in a task after a successful celery.Job
  task incorrectly prevented the job task from being marked as completed, with
  the errored task correctly put into an error state.
- Redirect to the next process task now will take into account tasks in the ERROR state
- Add ability to revive flow.Function and flow.SplitFirst
- Fixed an error that occurred when a deleted process.artifact was referenced in
  the process field data listing within templates.
- Allow to cancel Subprocess tasks
- Allow to cancel Function tasks
- Allow custom task models inherited from AbstactTask have no .seed and .data fields


2.2.5 2024-07-17
-----------------

- The 'pattern' widget attribute is now passed to the underlying form input.
- Fixed issue with flow image reload.
- Fixed dashboard max height on pages with long sidebars.
- Added .get_success_url(request) shortcut method to StartViewActivation and
  ViewActivation for convenient use in function-based views.
- Fixed duplicated task_finished signal on flow.View completion.
- Enabled callable defaults on jsonstore fields.
- Improved SVG and BPMN export shapes for SplitFirst and Timer Tasks.
- Created cookbook demo for comon workflow patterns

2.2.4 2024-07-12
-----------------

- Clone data, seed, and artifacts from canceled tasks to revived tasks.
- Enhance error handling for celery.Job.
- Improve the process cancellation template.
- Redirect to the task detail page after canceling or undoing actions, instead
  of redirecting to the process detail page.
- Added links to parent subprocess and parent task on the subprocess process and
  task details pages.
- Updated the Process.parent_task field to use related_name='subprocess',
  allowing access to subprocesses via task.subprocess
- Enhanced CreateProcessView and UpdateProcessView to set process_seed and
  artifact_generic_foreign_key fields based on form.cleaned_data, as Django
  model forms do not handle this automatically.
- Added tasks with an ERROR status to the process dashboard for better visibility and tracking.
- Added tooltip hover titles to nodes without text labels in the SVG workflow graph.
- Marked StartHandler nodes as BPMN Start Message events on the SVG graph.
- Fixed rendering of hidden field errors in forms.

2.2.3 2024-07-09
-----------------

- Fixed issue with Split/Join operations when an immediate split to join
  connection occurs.
- Improved redirect functionality for "Execute and Continue." Now redirects to
  the process details if the process has finished.
- Enabled the Undo action for End() nodes.


2.2.2 2024-07-05
----------------

- Introduced new parameters for .If().Then(.., task_data=, task_seed) and
  .Else(...)
- Include {{ form.media }} into default workflow/task.html template


2.2.1 2024-07-03
----------------

- Introduced a new parameter for .Next(..., task_seed=) that allows the
  instantiation of new tasks with additional initialized .seed generic foreign key
- Introduced a new parameter for .Split(..., task_seed_source=) same as task_data_source,
  prodices outgoing tasks with initializaed .seed value
- Introduced a new parameter for flow.Subprocess(process_data=, process_seed=,
  task_data=, task_seed=) allows to provide data nad seed for newly created
  process and/or start task

2.2.0 2024-06-28
----------------

- Introduced a new parameter for .Next(..., task_data=) that allows the
  instantiation of new tasks with additional initialized .data, enabling data to
  be passed from task to task.
- Added process.seed and task.seed generic foreign keys to the default workflow
  models. Along with process.artifact and task.artifact, these additions enable
  tracking of business process results from start to finish.
- Renamed Split.Next(data_source=) to task_data_source=.

2.1.3 2024-06-26
----------------

- Allow to use `flow.StartHandle` as start for subprocess
- Subprocess got get_subprocess_kwargs callable to provide additional parameters to flow.StartHandle

2.1.2 2024-06-24
----------------

- Allow cancelling Celery tasks from the ERROR state.
- Hotfix: Fix broken Join when no other nodes are created by Split.
- Allow using this references to flow static methods as Celery tasks.
- Allow cancelling Celery jobs from the ERROR status.
- Add missing permission check before adding a new item to the list.
- Allow Admin() viewset to be used as a sub-item in an Application viewset.

2.1.1 2024-06-06
----------------

- Hotfix broken task creation

2.1.0 2024-06-16
----------------

- Allow to assign additional custom data to viewflow.fsm transitions
- Added `data_source` parameter to `Split.Next()` method, allowing dynamic creation of multiple node instances based on a list of data items.


2.0.3 2024-05-11
----------------

- Fix task titles on the task details pages


2.0.2 2024-04-19
----------------

- Fix logout link
- Change admin user autocomplete field to readonly

2.0.1 2024-04-17
----------------

- Fix for AjaxModelSelect in m2m relations


2.0.0 2024-04-09
----------------

- Added support for Django 5.0+
- Updated to Material Components Web 1.4.0
- Improved help text styles
- Fixed default app_name configuration for Viewsets
- List View initial filter values support
- Enhanced localization support
- Corrected object permission checks for delete actions

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
