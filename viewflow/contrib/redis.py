import time
import random
from contextlib import contextmanager

from django.core.cache import cache
from django.db import transaction

from viewflow.exceptions import FlowLockFailed


try:
    import django_redis  # NOQA
except ImportError:
    raise ImportError('django-redis required')


def redis_lock(flow, attempts=5, expires=120):
    """
    Task lock based redis locks implemented in ``django-redis``.
    """

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
