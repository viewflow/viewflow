"""
Prevents inconsistent db updates for flow.
"""
import time
import random
from contextlib import contextmanager

from django.core.cache import DEFAULT_CACHE_ALIAS
from django.db import transaction, DatabaseError
from django.conf import settings

from viewflow.exceptions import FlowLockFailed


CACHE_BACKEND = getattr(settings, 'VIEWFLOW_LOCK_CACHE_BACKEND', DEFAULT_CACHE_ALIAS)
"""
Setting to change the cache backend for the cache based locks.

You may change the backend by defining ``VIEWFLOW_LOCK_CACHE_BACKEND``
in your settings.
The default cache backend is ``default``.
"""

try:
    from django.core.cache import caches
    cache = caches[CACHE_BACKEND]
except ImportError:  # Django 1.6
    from django.core.cache import get_cache
    cache = get_cache(CACHE_BACKEND)


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
                    if i != attempts-1:
                        sleep_time = (((i+1)*random.random()) + 2**i) / 2.5
                        time.sleep(sleep_time)
                    else:
                        raise FlowLockFailed('Lock failed for {}'.format(flow_cls))

            yield

    return lock


def cache_lock(flow, attempts=5, expires=120):
    """
    Use it if primary cache backend has transactional `add` functionality,
    like `memcached`.
    """
    @contextmanager
    def lock(flow_cls, process_pk):
        key = 'django-viewflow-lock-{}/{}'.format(flow_cls._meta.namespace, process_pk)

        for i in range(attempts):
            stored = cache.add(key, 1, expires)
            if stored:
                break
            if i != attempts-1:
                sleep_time = (((i+1)*random.random()) + 2**i) / 2.5
                time.sleep(sleep_time)
        else:
            raise FlowLockFailed('Lock failed for {}'.format(flow_cls))
        try:
            with transaction.atomic():
                yield
        finally:
            cache.delete(key)

    return lock


def redis_lock(flow, attempts=5, expires=120):
    """Task lock based redis locks implemented in ``django-redis``."""
    @contextmanager
    def lock(flow_cls, process_pk):
        key = 'django-viewflow-lock-{}/{}'.format(flow_cls._meta.namespace, process_pk)

        for i in range(attempts):
            lock = cache.lock(key, timeout=expires)
            stored = lock.acquire(blocking=False)
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
            lock.release()

    return lock
