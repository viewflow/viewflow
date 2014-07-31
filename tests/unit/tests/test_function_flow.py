from django.test import TestCase
from ..models import TestProcess
from ..flows import FunctionFlow


class TestSignalFlow(TestCase):
    def test_function_driven_flow(self):
        # start flow
        FunctionFlow.start.run()
        process = TestProcess.objects.first()

        # do the task
        FunctionFlow.task2.run(process)
        process = TestProcess.objects.first()

        # process should be finished
        self.assertEqual(TestProcess.STATUS.FINISHED, process.status)
        self.assertEqual(4, process.task_set.count())
