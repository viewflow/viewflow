=========
Changelog
=========

0.10.1 - 2016-03-24
-------------------

* flow.Start().Permission no longer supports callable (there is Start.Available for that)
* Task.flow_task and Task.owner_permission fields length extended up to 255 to match django Permission.name


0.10.0 - 2016-03-18
-------------------

* Django 1.9 support
* Admin can unassign view tasks
* Function and Handler nodes can use model methods via `this.method_name` references
* Added permission check on `viewflow.views.task.AssignView`
* Filter added to the `viewflow.view.ProcessListView`
* Fixed missing signals on Function/Signal task finished
* flow.lock is released if view code throws an exception
* Task.flow_process fixed in case of deep model inheritance
* flow.Signal now can skip signals without creating activation
* flow.Join now ignores incoming cancelled tasks tokens
* flow.End according to BPMN standard now doesn't cancel other active tasks
* {% include_process_data %} template tag now outputs a string repesention of FK to models from other apps
* All nodes now could have custom `task_description`
* Task.owner_permission column extended up to 150 characters
* *PRO ONLY* Obsolete nodes support, allows to delete a node from existing flows.
* *PRO ONLY* flow.Subprocess and flow.NSubprocess new nodes


0.9.0 - 2015-06-15
------------------

* Django 1.8 support
* Better inbox/queue views
* Improve undo/cancel tasks behaviour
* Allow to specify custom undo handlers methods
* Allow to use flow class methods as flow task functions
* Allow to list task state change handles in template
* *PRO ONLY* New Material Designed Frontend for the Flow

0.8.0 - 2014-12-02
------------------

* Development of viewform and karenina projects no longer opensourced
* Refactor fsm from task model to activation classes
* Generic admin actions for changing tasks state
* Support for view tasks unassign/reassign
* Allow tasks undo and cancel
* Store error information for tasks


0.7.0 - 2014-11-06
------------------

* Repository moved to https://github.com/viewflow/
* Form handling moved to separate library
* viewflow.site removed. Pro user still could install it with `pip install django-viewflow-site`
* Fancy ready to use templates available within Karenina project
* Tasks and Process list views became part of the viewflow library
* Flow urls simplified. Application instance namespaces not used anymore
* Fixed migrations for stable django 1.7
* HTTPS pypi server available for pro users.


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
