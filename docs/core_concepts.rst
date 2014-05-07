=============
Core concepts
=============

Flow and Flow Tasks
===================

django-viewflow introduces Flow classes as the single place to configure
and setup task, dependenices, persistance, user rights checking and interface setup.

Each flow should be subclass of :class:`viewflow.base.Flow`.

.. autoclass:: viewflow.base.Flow
   :members: urls

Each flow could contains several flow tasks. Flow task represents declaration
of what should be performed on this step, and what next steps should be activated.

Flow does not have specific declaration of task transitions, and all logic of task activation
belongs to the task itself. This makes Flow code close to well-known BPMN notation, and
helps to convert it to BPMN and vise versa.

Flow class should have at least one of :class:`viewflow.flow.Start` task and at least one of
:class:`viewflow.flow.End`

.. autoclass:: viewflow.flow.Node
   :members: activate

See :doc:`Flow Tasks <flow_tasks>` documentation for list of all available tasks.

Activation
==========

.. autoclass:: viewflow.activation.Activation
   :members: activate_next, activate

Models
======
django-viewflow provides base model for tracking the process state. In most cases you should
subclass :class:`viewflow.models.Process` to add additional data fields.

In case if you need to track some execution info or add logging, you can do it by
extending :class:`viewflow.models.Task`

.. autoclass:: viewflow.models.Task
   :members: assign, prepare, start, done

.. autoclass:: viewflow.models.Process
   :members: start, finish


Views
=====
.. autofunction:: viewflow.flow.start.flow_start_view
.. autoclass:: viewflow.flow.start.StartViewMixin
    :members: get_context_data, get_template_names, get_success_url, form_valid, dispatch
.. autoclass:: viewflow.flow.start.StartView
    :members: get_context_data, get_object, get_template_names, get_success_url, form_valid, dispatch

.. autofunction:: viewflow.flow.view.flow_view
.. autoclass:: viewflow.flow.view.TaskViewMixin
    :members: get_context_data, get_template_names, get_success_url, form_valid, dispatch
.. autoclass:: viewflow.flow.view.ProcessView
    :members: get_context_data, get_object, get_template_names, get_success_url, form_valid, dispatch

Urls
====
:class:`viewflow.base.Flow` collects all urls required by View tasks, you just
have to include it in urlpatters ::

  urlpatterns = patterns('',
        url(r'^myflow/', include(MyFlow.instance.urls)))
