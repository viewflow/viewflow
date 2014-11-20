import time
import unittest
import threading
import queue

from django.db import connection
from django.test import skipUnlessDBFeature

from viewflow import flow
from viewflow.base import Flow, this
from viewflow.exceptions import FlowLockFailed
from viewflow.lock import select_for_update_lock
from .. import integration_test


class NoTaskFlow(Flow):
    start = flow.Start().Next(this.end)
    end = flow.End()


@integration_test
class TestLocks(unittest.TestCase):
    def setUp(self):
        self.finished = False
        self.process = NoTaskFlow.process_cls.objects.create(flow_cls=NoTaskFlow)
        self.exception_queue = queue.Queue()

    def run_with_lock(self, lock):
        try:
            with lock(NoTaskFlow.end, self.process.pk):
                while not self.finished:
                    time.sleep(1)
        except FlowLockFailed as e:
            self.exception_queue.put(e)
        finally:
            connection.close()

    @skipUnlessDBFeature('has_select_for_update')
    def test_select_for_update_locks(self):
        lock = select_for_update_lock(NoTaskFlow, attempts=1)
        with lock(NoTaskFlow.end, self.process.pk):
            pass

        thread1 = threading.Thread(target=self.run_with_lock, args=[select_for_update_lock(NoTaskFlow, attempts=1)])
        thread2 = threading.Thread(target=self.run_with_lock, args=[select_for_update_lock(NoTaskFlow, attempts=1)])

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
