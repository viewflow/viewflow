import time
import unittest
import threading
import queue

from django.db import connection
from django.test import skipUnlessDBFeature

from viewflow import flow, lock
from viewflow.base import Flow, this
from viewflow.exceptions import FlowLockFailed


class Test(unittest.TestCase):
    class TestFlow(Flow):
        start = flow.Start().Next(this.end)
        end = flow.End()

    def setUp(self):
        self.finished = False
        self.process = Test.TestFlow.process_cls.objects.create(flow_cls=Test.TestFlow)
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

    @skipUnlessDBFeature('has_select_for_update')
    def test_select_for_update_locks(self):
        thread1 = threading.Thread(target=self.run_with_lock, args=[lock.select_for_update_lock(Test.TestFlow, attempts=1)])
        thread2 = threading.Thread(target=self.run_with_lock, args=[lock.select_for_update_lock(Test.TestFlow, attempts=1)])

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

    def test_cache_lock(self):
        thread1 = threading.Thread(target=self.run_with_lock, args=[lock.cache_lock(Test.TestFlow, attempts=1)])
        thread2 = threading.Thread(target=self.run_with_lock, args=[lock.cache_lock(Test.TestFlow, attempts=1)])

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

    def test_redis_lock(self):
        thread1 = threading.Thread(target=self.run_with_lock, args=[lock.redis_lock(Test.TestFlow, attempts=1)])
        thread2 = threading.Thread(target=self.run_with_lock, args=[lock.redis_lock(Test.TestFlow, attempts=1)])

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


