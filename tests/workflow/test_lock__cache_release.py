from django.core.cache import cache
from django.test import TestCase

from viewflow import this
from viewflow.workflow import flow, lock


class Test(TestCase):
    def _key(self, process_pk):
        return "django-viewflow-lock-{}/{}".format(
            TestCacheReleaseFlow.instance.flow_label, process_pk
        )

    def tearDown(self):
        cache.delete(self._key(1))
        cache.delete(self._key(2))

    def test_release_does_not_delete_a_foreign_lock(self):
        # CacheLock's fixed `expires` TTL is decoupled from the operation's
        # real duration: once it lapses mid-operation, another worker's
        # cache.add succeeds on the key. The unconditional
        # `finally: cache.delete(key)` then destroyed that *new* holder's
        # lock, letting a third worker in -- every overrun cascaded. Release
        # must be ownership-guarded, exactly as contrib.redis's RedisLock
        # already is.
        lock_impl = lock.CacheLock(attempts=1)

        with lock_impl(TestCacheReleaseFlow, 1):
            # Simulate the TTL expiring mid-operation and a competing worker
            # acquiring the same key (deterministic, no timing dependency).
            cache.delete(self._key(1))
            self.assertTrue(cache.add(self._key(1), "foreign-token", 100))

        self.assertEqual(
            cache.get(self._key(1)),
            "foreign-token",
            "releasing an expired lock must not delete the new holder's key",
        )

    def test_release_deletes_the_lock_it_owns(self):
        lock_impl = lock.CacheLock(attempts=1)

        with lock_impl(TestCacheReleaseFlow, 2):
            self.assertIsNotNone(cache.get(self._key(2)))

        self.assertIsNone(cache.get(self._key(2)))
        # and the key is immediately re-acquirable
        with lock_impl(TestCacheReleaseFlow, 2):
            pass


class TestCacheReleaseFlow(flow.Flow):  # noqa: D101
    start = flow.StartHandle().Next(this.end)
    end = flow.End()
