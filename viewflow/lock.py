import time
import random
import warnings
from contextlib import contextmanager

from django.core.cache import cache
from django.db import transaction, DatabaseError

from viewflow.exceptions import FlowLockFailedException


def no_lock():
    @contextmanager
    def lock(flow_task, act_id, wait=True):
        warnings.warn('No locking on flow', RuntimeWarning)
        yield
    return lock


def select_for_update_lock(using=None, nowait=True, attempts=5):
    @contextmanager
    def lock(flow_task, act_id):
        assert not transaction.get_autocommit(using=using)

        process_ids = flow_task.flow_cls.task_cls._default_manager.filter(pk=act_id).values('process_id')
        for i in range(attempts):
            try:
                flow_task.flow_cls.process_cls._default_manager \
                    .filter(id__in=process_ids) \
                    .select_for_update(nowait=nowait) \
                    .exists()
                break
            except DatabaseError:
                if i != attempts-1:
                    sleep_time = (((i+1)*random.random()) + 2**i) / 2.5
                    time.sleep(sleep_time)
        else:
            raise FlowLockFailedException('Lock failed for {}'.format(flow_task.name))

        yield

    return lock


def cache_lock(attempts=5, expires=120):
    """
    Use it if primary cache backend have transactional add functionallity
    """
    @contextmanager
    def lock(flow_task, act_id):
        key = 'django-viewflow-lock-{}.{}/{}'.format(flow_task.flow_cls._meta.namespace, flow_task.name, act_id)

        for i in range(attempts):
            stored = cache.add(key, 1, expires)
            if stored:
                break
            if i != attempts-1:
                sleep_time = (((i+1)*random.random()) + 2**i) / 2.5
                time.sleep(sleep_time)
        else:
            raise FlowLockFailedException('Lock failed for {}'.format(flow_task.name))

        yield

        cache.delete(key)

    return lock
