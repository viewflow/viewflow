"""Prevents inconsistent db updates for flow."""
from __future__ import unicode_literals

import time
import random
from contextlib import contextmanager

from django.core.cache import cache as default_cache
from django.db import transaction, DatabaseError

from .exceptions import FlowLockFailed


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
                    process = flow_class.process_class._default_manager.filter(pk=process_pk)
                    process.select_for_update(nowait=self.nowait).exists()
                except DatabaseError:
                    if i != self.attempts - 1:
                        sleep_time = (((i + 1) * random.random()) + 2 ** i) / 2.5
                        time.sleep(sleep_time)
                    else:
                        raise FlowLockFailed('Lock failed for {}'.format(flow_class))
                else:
                    yield
                    break


class CacheLock(object):
    """
    Task lock based on Django cache.

    Use it if primary cache backend has transactional `add` functionality,
    like `memcached`.

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
        key = 'django-viewflow-lock-{}/{}'.format(flow_class.instance.flow_label, process_pk)

        for i in range(self.attempts):
            if self.cache.add(key, 1, self.expires):
                break
            if i != self.attempts - 1:
                sleep_time = (((i + 1) * random.random()) + 2 ** i) / 2.5
                time.sleep(sleep_time)
        else:
            raise FlowLockFailed('Lock failed for {}'.format(flow_class))

        try:
            with transaction.atomic():
                yield
        finally:
            self.cache.delete(key)


no_lock = NoLock()
cache_lock = CacheLock()
select_for_update_lock = SelectForUpdateLock()
