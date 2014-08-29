from unittest import mock
from django.test import TestCase
from celery import shared_task

from viewflow import activation, flow
from viewflow.models import Task
from viewflow.contrib import celery


@shared_task()
@flow.flow_job()
def failure_job(activation):
    raise NotImplementedError


@shared_task()
@flow.flow_job()
def successful_job(activation):
    pass


class TestJobActivation(TestCase):
    def test_failed_job(self):
        task_mock = mock.Mock(spec=Task())
        flow_task_mock = mock.MagicMock(spec=celery.Job(lambda p: None))
        flow_task_mock.flow_cls.task_cls.objects.get = mock.Mock(return_value=task_mock)
        flow_task_mock.activation_cls = mock.Mock(return_value=celery.JobActivation())

        with mock.patch('viewflow.flow.job.import_task_by_ref', return_value=flow_task_mock):
            with self.assertRaises(NotImplementedError):
                failure_job(flow_task_strref='unit/TestFlow.job', process_pk=-1, task_pk=-1)

        task_mock.prepare.assert_called_once_with()
        task_mock.start.assert_called_once_with()
        task_mock.error.assert_called_once_with()
        self.assertFalse(task_mock.done.called)

    def test_failed_activate_next(self):
        job_task_mock = mock.Mock(spec=Task())
        gate_task_mock = mock.Mock(spec=Task())

        next_flow_task_mock = mock.Mock()
        next_flow_task_mock.flow_cls.task_cls = mock.Mock(return_value=gate_task_mock)
        next_flow_task_mock.dst.activate = \
            lambda prev_activation, token: activation.GateActivation().activate(next_flow_task_mock, prev_activation, token)  # NOQA

        flow_task_mock = mock.MagicMock(spec=celery.Job(lambda p: None))
        flow_task_mock.flow_cls.task_cls.objects.get = mock.Mock(return_value=job_task_mock)
        flow_task_mock.activation_cls = mock.Mock(return_value=celery.JobActivation())
        flow_task_mock._outgoing = mock.Mock(return_value=[next_flow_task_mock])

        with mock.patch('viewflow.flow.job.import_task_by_ref', return_value=flow_task_mock):
            successful_job(flow_task_strref='unit/TestFlow.job', process_pk=-1, task_pk=-1)

        job_task_mock.prepare.assert_called_once_with()
        job_task_mock.start.assert_called_once_with()
        job_task_mock.done.assert_called_once_with()
        self.assertFalse(job_task_mock.error.called)

        gate_task_mock.prepare.assert_called_once_with()
        gate_task_mock.error.assert_called_once_with()
        self.assertFalse(gate_task_mock.done.called)
