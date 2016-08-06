from __future__ import print_function

import os
import queue
import threading
import time
import unittest

import django
from django.db import connection
from django.test import TestCase
from django.test.utils import override_settings

from viewflow import flow
from viewflow.base import Flow, this
from viewflow.contrib import redis
from viewflow.exceptions import FlowLockFailed


@unittest.skipUnless('REDIS_CACHE_URL' in os.environ, 'Celery test requires redis server url')
@unittest.skipUnless(django.VERSION >= (1, 7), 'django>=1.7 required')
@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": os.environ.get('REDIS_CACHE_URL'),
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }
)
class Test(TestCase):
    class TestFlow(Flow):
        start = flow.Start().Next(this.end)
        end = flow.End()

    def setUp(self):
        self.finished = False
        self.process = Test.TestFlow.process_class.objects.create(flow_class=Test.TestFlow)
        self.exception_queue = queue.Queue()

    def run_with_lock(self, lock_impl):
        try:
            with lock_impl(Test.TestFlow, self.process.pk):
                while not self.finished:
                    time.sleep(0.001)
        except FlowLockFailed as e:
            self.exception_queue.put(e)
        finally:
            connection.close()

    def test_redis_lock(self):
        thread1 = threading.Thread(target=self.run_with_lock, args=[redis.redis_lock(Test.TestFlow, attempts=1)])
        thread2 = threading.Thread(target=self.run_with_lock, args=[redis.redis_lock(Test.TestFlow, attempts=1)])

        thread1.start()
        thread2.start()

        try:
            self.exception_queue.get(True, 10)
        except queue.Empty:
            self.fail('No thread was blocked')
        finally:
            self.finished = True

        thread1.join()
        thread2.join()
