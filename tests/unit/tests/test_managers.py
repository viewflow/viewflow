from django.test import TestCase
from viewflow.models import Process, Task
from ..flows import FunctionFlow
from ..models import TestProcess


class Test(TestCase):
    def test_task_manager_coerce_to_self(self):
        FunctionFlow.start.run()
        tasks = Task.objects.coerce_for([FunctionFlow])
        self.assertTrue(all(isinstance(task, Task) for task in tasks))

    def test_process_manager_coerce_to_custom_model(self):
        FunctionFlow.start.run()
        processes = Process.objects.coerce_for([FunctionFlow])
        self.assertTrue(all(isinstance(process, TestProcess) for process in processes))
