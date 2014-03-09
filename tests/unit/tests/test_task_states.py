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
        # switch
        # split
        # join
        # first
        # timer
        # mailbox
        # end

        
