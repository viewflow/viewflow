from django.test import TransactionTestCase
from django.test.utils import override_settings
from viewflow.models import Task

from unit.flows import AllTaskFlow
from unit.helpers import get_default_form_data


@override_settings(CELERY_ALWAYS_EAGER=True)
class TestFlowTaskStates(TransactionTestCase):
    available_apps = ['viewflow', 'unit']

    def test_all_activations_succeed(self):
        # start
        activation = AllTaskFlow.start.start()
        activation = AllTaskFlow.start.start(get_default_form_data(activation.form))
        AllTaskFlow.start.done(activation)

        # view
        task = Task.objects.get(flow_task=AllTaskFlow.view)
        activation = AllTaskFlow.view.start(task)
        activation = AllTaskFlow.view.start(task, get_default_form_data(activation.form))
        AllTaskFlow.view.done(activation)

        # job
        task = Task.objects.get(flow_task=AllTaskFlow.job)
        self.assertIsNotNone(task.finished)  # Celery executed eager

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

