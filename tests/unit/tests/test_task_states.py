from django.test import TestCase
from viewflow.models import Activation
from unit.flows import AllTaskFlow


class TestFlowTaskStates(TestCase):
    def test_all_activations_succeed(self):
        # start
        activation = AllTaskFlow.start.start()
        AllTaskFlow.start.done(activation)

        # view
        activation = Activation.objects.get(flow_task=AllTaskFlow.view)
        activation = AllTaskFlow.view.start(activation.pk)
        AllTaskFlow.view.done(activation)

        # job
        activation = Activation.objects.get(flow_task=AllTaskFlow.job)
        activation = AllTaskFlow.job.start(activation.pk)
        AllTaskFlow.job.done(activation)

        # iff
        activation = Activation.objects.get(flow_task=AllTaskFlow.iff)
        self.assertIsNotNone(activation.finished)

        # switch
        activation = Activation.objects.get(flow_task=AllTaskFlow.switch)
        self.assertIsNotNone(activation.finished)

        # split
        activation = Activation.objects.get(flow_task=AllTaskFlow.switch)
        self.assertIsNotNone(activation.finished)

        # join
        activation = Activation.objects.get(flow_task=AllTaskFlow.join)
        self.assertIsNotNone(activation.finished)

        # first
        # timer
        # mailbox
        # end

