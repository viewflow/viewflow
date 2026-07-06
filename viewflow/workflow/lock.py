"""Prevents inconsistent db updates for flow."""

from __future__ import unicode_literals

import threading
import time
import random
import uuid
from contextlib import contextmanager

from django.core.cache import cache as default_cache
from django.db import transaction, DatabaseError

from .exceptions import FlowLockFailed


_deferred = threading.local()


def after_lock_released(callback):
    """Run ``callback`` once every flow lock held by this thread is released,
    or immediately when no flow lock is held.

    Work that needs a *different* process's lock (e.g. completing a finished
    subprocess's parent task) must not acquire it nested inside a held one:
    that re-enters the same key for a synchronous subprocess (which a
    non-reentrant lock like CacheLock fails outright) and, in the async case,
    takes child-then-parent -- the inverse of the cancel path's
    parent-then-child order, a deadlock under concurrency.
    """
    queue = getattr(_deferred, "queue", None)
    if queue is None:
        callback()
    else:
        queue.append(callback)


@contextmanager
def lock_scope(lock_impl, flow_class, process_pk):
    """Acquire ``lock_impl`` and, once the outermost lock in this thread is
    released, run the callbacks queued via :func:`after_lock_released`."""
    outermost = getattr(_deferred, "queue", None) is None
    if outermost:
        _deferred.queue = []
    try:
        with lock_impl(flow_class, process_pk):
            yield
    finally:
        if outermost:
            callbacks = _deferred.queue
            _deferred.queue = None
            # Callbacks re-read state under their own fresh lock, so running
            # them after a failed scope is safe -- a rolled-back precondition
            # just makes them a no-op.
            for callback in callbacks:
                callback()


class NoLock(object):
    """
    No pessimistic locking, just execute flow task in transaction.

    Not suitable when you have Join nodes in your flow.
    """

    @contextmanager
    def __call__(self, flow_class, process_pk):
        with transaction.atomic():
            yield


class SelectForUpdateLock(object):
    """
    Database lock uses `select ... for update` on the process instance row.

    Recommended to use with PostgreSQL.
    """

    def __init__(self, nowait=True, attempts=5):
        self.nowait = nowait
        self.attempts = attempts

    @contextmanager
    def __call__(self, flow_class, process_pk):
        for i in range(self.attempts):
            with transaction.atomic():
                try:
                    process = flow_class.process_class._default_manager.filter(
                        pk=process_pk
                    )
                    process.select_for_update(nowait=self.nowait).exists()
                except DatabaseError:
                    if i != self.attempts - 1:
                        sleep_time = (((i + 1) * random.random()) + 2**i) / 2.5
                        time.sleep(sleep_time)
                    else:
                        raise FlowLockFailed("Lock failed for {}".format(flow_class))
                else:
                    yield
                    break


class CacheLock(object):
    """
    Task lock based on Django cache.

    Use it if primary cache backend has transactional `add` functionality,
    like `memcached` or Redis. A per-process backend like ``LocMemCache``
    provides no cross-worker mutual exclusion.

    ``expires`` must exceed the longest operation ever run under the lock:
    once the TTL lapses the key silently drops and another worker can
    acquire it while the first is still running.

    Example::

        class MyFlow(Flow):
            lock_impl = CacheLock(cache=caches['locks'])

    The example uses a different cache. The default cache
    is Django ``default`` cache configuration.
    """

    def __init__(self, cache=default_cache, attempts=5, expires=120):  # noqa D102
        self.cache = cache
        self.attempts = attempts
        self.expires = expires

    @contextmanager
    def __call__(self, flow_class, process_pk):  # noqa D102
        key = "django-viewflow-lock-{}/{}".format(
            flow_class.instance.flow_label, process_pk
        )
        token = str(uuid.uuid4())

        for i in range(self.attempts):
            if self.cache.add(key, token, self.expires):
                break
            if i != self.attempts - 1:
                sleep_time = (((i + 1) * random.random()) + 2**i) / 2.5
                time.sleep(sleep_time)
        else:
            raise FlowLockFailed("Lock failed for {}".format(flow_class))

        try:
            with transaction.atomic():
                yield
        finally:
            # After `expires`, the key may already belong to another worker;
            # deleting it unconditionally would destroy *their* lock and
            # cascade the mutual-exclusion loss. Ownership-guarded release
            # (best-effort -- the plain cache API has no compare-and-delete).
            if self.cache.get(key) == token:
                self.cache.delete(key)


no_lock = NoLock()
cache_lock = CacheLock()
select_for_update_lock = SelectForUpdateLock()
