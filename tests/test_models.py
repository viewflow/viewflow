from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.timezone import now

from viewflow import flow
from viewflow.base import Flow
from viewflow.models import Process, Task


class Test(TestCase):
    def test_process_refresh_from_db_backport(self):
        process = Process.objects.create(flow_class=Flow)
        self.assertIsNone(process.finished)

        Process.objects.filter(pk=process.pk).update(finished=now())
        process.refresh_from_db()
        self.assertIsNotNone(process.finished)

    def test_process_create_by(self):
        user = User.objects.create(username='Test')
        process = Process.objects.create(flow_class=Flow)
        Task.objects.create(process=process, flow_task=GrandChildFlow.start, owner=user)

        self.assertEqual(process.created_by, user)

    def test_task_get_real_process_class(self):
        process = TestModelsGrandChildProcess.objects.create(flow_class=GrandChildFlow)
        task = Task.objects.create(process=process, flow_task=GrandChildFlow.start)

        # can't user refresh_from_db() here, task.process is not updated to correct base class
        task = Task.objects.get(pk=task.pk)

        self.assertIsInstance(task.flow_process, TestModelsGrandChildProcess)
        self.assertEqual(task.flow_process, process)


class TestModelsChildProcess(Process):
    pass


class TestModelsGrandChildProcess(TestModelsChildProcess):
    pass


class GrandChildFlow(Flow):
    process_class = TestModelsGrandChildProcess

    start = flow.Start(lambda rewquest: None)
