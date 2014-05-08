"""
Prevents unconsistent db updates for flow.
"""
import time
import random
import warnings
from contextlib import contextmanager

from django.core.cache import cache
from django.db import transaction, DatabaseError

from viewflow.exceptions import FlowLockFailed


def no_lock():
    """
    By default Flow has no locking.
    """
    @contextmanager
    def lock(flow_task, process_pk):
        warnings.warn('No locking on flow', RuntimeWarning)
        yield
    return lock


def select_for_update_lock(nowait=True, attempts=5):
    """
    Uses `select ... for update` on process instance row for locking,
    bound to database transaction.

    Recommended for use with PostgreSQL.
    """
    @contextmanager
    def lock(flow_task, process_pk):
        assert transaction.get_autocommit() or transaction.commit.__module__ == 'django.test.testcases'

        with transaction.atomic():
            for i in range(attempts):
                try:
                    flow_task.flow_cls.process_cls._default_manager \
                        .filter(pk=process_pk) \
                        .select_for_update(nowait=nowait) \
                        .exists()
                    break
                except DatabaseError:
                    if i != attempts-1:
                        sleep_time = (((i+1)*random.random()) + 2**i) / 2.5
                        time.sleep(sleep_time)
                    else:
                        raise FlowLockFailed('Lock failed for {}'.format(flow_task.name))

            yield

    return lock


def cache_lock(attempts=5, expires=120):
    """
    Use it if primary cache backend has transactional `add` functionality,
    like `memcached`.
    """
    @contextmanager
    def lock(flow_task, process_pk):
        key = 'django-viewflow-lock-{}.{}/{}'.format(flow_task.flow_cls._meta.namespace, flow_task.name, process_pk)

        for i in range(attempts):
            stored = cache.add(key, 1, expires)
            if stored:
                break
            if i != attempts-1:
                sleep_time = (((i+1)*random.random()) + 2**i) / 2.5
                time.sleep(sleep_time)
        else:
            raise FlowLockFailed('Lock failed for {}'.format(flow_task.name))

        with transaction.atomic():
            yield

        cache.delete(key)

    return lock
