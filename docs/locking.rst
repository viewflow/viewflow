=======
Locking
=======
To avoid raise conditions on update :func:`viewflow.flow.flow_view` and
:func:`viewflow.flow.flow_job` decoratos grabs process-instance wide
locks and instansiate database transaction.

You could specify selected lock implementation in :attr:lock_impl of
:class:`viewflow.base.Flow` class

.. autofunction:: viewflow.lock.no_lock

.. autofunction:: viewflow.lock.select_for_update_lock

.. autofunction:: viewflow.lock.cache_lock
