==========
Flow tasks
==========


Start
=====
.. autoclass:: viewflow.flow.Start
   :members: Permission, Available


View
====
View task represents user task performed by interaction with django view.

.. autoclass:: viewflow.flow.View
   :members: Permission, Assign

.. autofunction:: viewflow.flow.flow_view

Views decorated with `flow_view` decorator executed in transaction. If an error happens in view or
during nexttask activation, database rollback will be performed and no changes will be stored.

Job
===
Job task represents user task performed in background by celery

.. autoclass:: viewflow.flow.Job

.. autofunction:: viewflow.flow.flow_job

If any error will happens during job execution task would be moved to `error` state, and available
for administrator desision in admin interface. If error will happens on next task ativation, for
example, error raised on `If` conditions, job task will be commited and marked as done, but the
failed for activation task would be created in `error` state.


If
===
.. autoclass:: viewflow.flow.If

Switch
======
.. autoclass:: viewflow.flow.Switch


Split
=====
.. autoclass:: viewflow.flow.Split

Join
====
.. autoclass:: viewflow.flow.Join

End
====
.. autoclass:: viewflow.flow.End

