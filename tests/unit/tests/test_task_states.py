from django.test import TestCase
from viewflow.models import Task
from unit.flows import AllTaskFlow


class TestFlowTaskStates(TestCase):
    def test_all_activations_succeed(self):
        # start
        activation = AllTaskFlow.start.start()
        AllTaskFlow.start.done(activation)

        # view
        task = Task.objects.get(flow_task=AllTaskFlow.view)
        task = AllTaskFlow.view.start(task.pk)
        AllTaskFlow.view.done(task)

        # job
        task = Task.objects.get(flow_task=AllTaskFlow.job)
        task = AllTaskFlow.job.start(task.pk)
        AllTaskFlow.job.done(task)

        # iff
        task = Task.objects.get(flow_task=AllTaskFlow.iff)
        self.assertIsNotNone(task.finished)

        # switch
        task = Task.objects.get(flow_task=AllTaskFlow.switch)
        self.assertIsNotNone(task.finished)

        # split
        task = Task.objects.get(flow_task=AllTaskFlow.switch)
        self.assertIsNotNone(task.finished)

        # join
        task = Task.objects.get(flow_task=AllTaskFlow.join)
        self.assertIsNotNone(task.finished)

        # first
        # timer
        # mailbox
        # end

