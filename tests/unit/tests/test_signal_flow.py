from django.test import TestCase
from ..models import TestProcess
from ..signals import test_start_flow, test_done_flow_task


class TestSignalFlow(TestCase):
    def test_signal_driven_flow(self):
        # start flow
        test_start_flow.send(sender=self, message='Test')
        process = TestProcess.objects.first()

        # do the task
        test_done_flow_task.send(sender=process, message='Test')
        process = TestProcess.objects.first()

        # process should be finished
        self.assertEqual(TestProcess.STATUS.FINISHED, process.status)
        self.assertEqual(3, process.task_set.count())
