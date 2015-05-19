from django.test import TestCase
from ..flows import FunctionFlow, DefaultProcessFunctionFlow


class Test(TestCase):
    def test_get_real_process(self):
        FunctionFlow.start.run()
        task = FunctionFlow.task_cls.objects.all()[0]
        self.assertTrue(isinstance(task.flow_process, FunctionFlow.process_cls))

    def test_get_real_process_nohop(self):
        DefaultProcessFunctionFlow.start.run()
        task = DefaultProcessFunctionFlow.task_cls.objects.all()[0]
        self.assertTrue(isinstance(task.flow_process, DefaultProcessFunctionFlow.process_cls))
