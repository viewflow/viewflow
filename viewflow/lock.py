"""
Prevents inconsistent db updates for flow.
"""
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
    def lock(flow_cls, process_pk):
        with transaction.atomic():
            yield
    return lock


def select_for_update_lock(flow, nowait=True, attempts=5):
    """
    Uses `select ... for update` on process instance row for locking,
    bound to database transaction.

    Recommended for use with PostgreSQL.
    """
    @contextmanager
    def lock(flow_cls, process_pk):
        with transaction.atomic():
            for i in range(attempts):
                try:
                    flow_cls.process_cls._default_manager \
                        .filter(pk=process_pk) \
                        .select_for_update(nowait=nowait) \
                        .exists()
                    break
                except DatabaseError:
                    if i != attempts - 1:
                        sleep_time = (((i + 1) * random.random()) + 2 ** i) / 2.5
                        time.sleep(sleep_time)
                    else:
                        raise FlowLockFailed('Lock failed for {}'.format(flow_cls))

            yield

    return lock


class CacheLock(object):
    """
    Task lock based on Django's cache.

    Example::

        class MyFlow(Flow):
            lock_impl = RedisLock(cache=caches['locks'])

    The example uses a different cache. The default cache
    is Django's ``default`` cache configuration.
    """

    def __init__(self, cache=default_cache):
        self.cache = cache

    def __call__(self, flow, attempts=5, expires=120):
        cache = self.cache

        @contextmanager
        def lock(flow_cls, process_pk):
            key = 'django-viewflow-lock-{}/{}'.format(flow_cls._meta.namespace, process_pk)

            for i in range(attempts):
                stored = cache.add(key, 1, expires)
                if stored:
                    break
                if i != attempts - 1:
                    sleep_time = (((i + 1) * random.random()) + 2 ** i) / 2.5
                    time.sleep(sleep_time)
            else:
                raise FlowLockFailed('Lock failed for {}'.format(flow_cls))

            try:
                with transaction.atomic():
                    yield
            finally:
                cache.delete(key)

        return lock


cache_lock = CacheLock()
"""
Use it if primary cache backend has transactional `add` functionality,
like `memcached`.
"""
