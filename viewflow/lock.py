"""Prevents inconsistent db updates for flow."""

import time
import random
from contextlib import contextmanager

from django.core.cache import cache as default_cache
from django.db import transaction, DatabaseError

from viewflow.exceptions import FlowLockFailed


def no_lock(flow):
    """
    No pessimistic locking, just execute flow task in transaction.

    Not suitable when you have Join nodes in your flow.
    """
    @contextmanager
    def lock(flow_class, process_pk):
        with transaction.atomic():
            yield
    return lock


def select_for_update_lock(flow, nowait=True, attempts=5):
    """
    Databace lock uses `select ... for update` on the process instance row.

    Recommended to use with PostgreSQL.
    """
    @contextmanager
    def lock(flow_class, process_pk):
        for i in range(attempts):
            with transaction.atomic():
                try:
                    process = flow_class.process_class._default_manager.filter(pk=process_pk)
                    if not process.select_for_update(nowait=nowait).exists():
                        raise DatabaseError('Process not exists')
                except DatabaseError:
                    if i != attempts - 1:
                        sleep_time = (((i + 1) * random.random()) + 2 ** i) / 2.5
                        time.sleep(sleep_time)
                    else:
                        raise FlowLockFailed('Lock failed for {}'.format(flow_class))
                else:
                    yield
                    break
    return lock


class CacheLock(object):
    """
    Task lock based on Django's cache.

    Use it if primary cache backend has transactional `add` functionality,
    like `memcached`.

    Example::

        class MyFlow(Flow):
            lock_impl = RedisLock(cache=caches['locks'])

    The example uses a different cache. The default cache
    is Django's ``default`` cache configuration.
    """

    def __init__(self, cache=default_cache):  # noqa D102
        self.cache = cache

    def __call__(self, flow, attempts=5, expires=120):  # noqa D102
        cache = self.cache

        @contextmanager
        def lock(flow_class, process_pk):
            key = 'django-viewflow-lock-{}/{}'.format(flow_class._meta.flow_label, process_pk)

            for i in range(attempts):
                process = flow_class.process_class._default_manager.filter(pk=process_pk)
                if process.exists():
                    stored = cache.add(key, 1, expires)
                    if stored:
                        break
                if i != attempts - 1:
                    sleep_time = (((i + 1) * random.random()) + 2 ** i) / 2.5
                    time.sleep(sleep_time)
            else:
                raise FlowLockFailed('Lock failed for {}'.format(flow_class))

            try:
                with transaction.atomic():
                    yield
            finally:
                cache.delete(key)

        return lock


cache_lock = CacheLock()
