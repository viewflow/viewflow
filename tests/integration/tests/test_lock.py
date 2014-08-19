import time
import sys
import threading
import unittest
try:
    import queue
except:
    import Queue as queue

from django.db import connection
from viewflow.exceptions import FlowLockFailed
from viewflow.lock import select_for_update_lock
from ..flows import NoTaskFlow


@unittest.skipIf('integration' not in sys.argv, reason='Integration Test')
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

    def test_select_for_update_locks(self):
        thread1 = threading.Thread(target=self.run_with_lock, args=[select_for_update_lock(attempts=1)])
        thread2 = threading.Thread(target=self.run_with_lock, args=[select_for_update_lock(attempts=1)])

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
