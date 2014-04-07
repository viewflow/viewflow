from unittest.mock import patch
from django.test import TransactionTestCase
from django.test.utils import override_settings
from viewflow.models import Task

from unit.flows import AllTaskFlow
from unit.helpers import get_default_form_data
from unit.tasks import dummy_job


@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True)
class TestFlowTaskStates(TransactionTestCase):
    available_apps = ['viewflow', 'unit']

    @patch('unit.tasks.dummy_job.apply_async')
    def test_all_activations_succeed(self, dummy_job_apply_async):
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

        expected_job_kwargs = {
            'args': ['unit/flows.AllTaskFlow.job', task.process_id, task.pk],
            'task_id': task.external_task_id,
            'countdown': 1}

        dummy_job_apply_async.assert_called_once_with(**expected_job_kwargs)

        dummy_job.apply(**expected_job_kwargs)
        task = Task.objects.get(flow_task=AllTaskFlow.job)
        self.assertIsNotNone(task.finished)

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

