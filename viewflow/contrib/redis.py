import time
import random
from contextlib import contextmanager

from django.core.cache import cache as default_cache
from django.db import transaction

from viewflow.exceptions import FlowLockFailed


try:
    import django_redis  # NOQA
except ImportError:
    raise ImportError('django-redis required')


class RedisLock(object):
    """
    Task lock based on redis' cache capabilities.

    Example::

        class MyFlow(Flow):
            lock_impl = RedisLock(cache=caches['locks'])

    The example uses a different cache. The default cache
    is Django's ``default`` cache configuration.

    ..note::
        This lock requires a ``django-redis`` cache backend.

    """

    def __init__(self, cache=default_cache):
        self.cache = cache

    def __call__(self, flow, attempts=5, expires=120):
        cache = self.cache

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


redis_lock = RedisLock()
"""Task lock requires the default cache config to use a ``django-redis`` cache backend."""
