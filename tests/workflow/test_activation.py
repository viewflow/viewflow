from django.test import TestCase
from viewflow.workflow import STATUS
from viewflow.workflow.models import Process, Task
from viewflow.workflow.activation import Activation


class Test(TestCase):  # noqa: D101
    def test_lifecycle(self):
        process = Process()
        task = Task(process=process, status=STATUS.NEW)
        activation = Activation(task)
        transitions = activation.get_outgoing_transitions()
        self.assertEqual(2, len(transitions))
