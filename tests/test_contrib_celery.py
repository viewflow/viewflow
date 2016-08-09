from __future__ import print_function

import os
import subprocess
import unittest
import sys
import time

from django.db import models, connection
from django.utils.decorators import method_decorator
from django.test import TransactionTestCase

from viewflow import flow
from viewflow.activation import STATUS
from viewflow.base import Flow, this
from viewflow.contrib import celery
from viewflow.models import Process, Task

from tests import celery_app


@unittest.skipUnless('DATABASE_URL' in os.environ, 'Celery test requires specific database config')
class Test(TransactionTestCase):
    def setUp(self):
        """Start celery worker connection the the test database"""
        env = os.environ.copy()
        database_url = env['DATABASE_URL']
        env['DATABASE_URL'] = '{}/{}'.format(
            database_url[:database_url.rfind('/')], connection.settings_dict['NAME'])

        cmd = ['celery', 'worker', '-A', 'tests.celery_app', '-l', 'debug']

        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        self.assertIsNone(self.process.poll())

    def tearDown(self):
        self.process.kill()
        if '-v3' in sys.argv:
            stdout, stderr = self.process.communicate()
            print(' CELERY STDOUT '.center(80, '='))
            print(stdout.decode())

            print(' CELERY STDERR '.center(80, '='), file=sys.stderr)
            print(stderr.decode(), file=sys.stderr)

    def wait_for_task(self, process, flow_task, status=None):
        for _ in range(100):
            try:
                return process.get_task(flow_task, status=status)
            except Task.DoesNotExist:
                time.sleep(0.05)
        assert False, 'Task {} not found'.format(flow_task)

    def test_flow_succeed(self):
        activation = TestCeleryFlow.start.run(throw_error=False)

        self.wait_for_task(activation.process, TestCeleryFlow.task, status=STATUS.DONE)

        process = TestCeleryProcess.objects.get(pk=activation.process.pk)
        self.assertEqual(STATUS.DONE, process.status)

    def test_flow_failed(self):
        activation = TestCeleryFlow.start.run(throw_error=True)
        task = self.wait_for_task(activation.process, TestCeleryFlow.task, status=STATUS.ERROR)

        process = TestCeleryProcess.objects.get(pk=task.process_id)
        process.throw_error = False
        process.save()

        task.activate().retry()

        task = self.wait_for_task(activation.process, TestCeleryFlow.task, status=STATUS.DONE)

        process = TestCeleryProcess.objects.get(pk=task.process_id)
        self.assertEqual(STATUS.DONE, process.status)

    def test_flow_retry(self):
        activation = TestCeleryRetryFlow.start.run(throw_error=True)

        self.wait_for_task(activation.process, TestCeleryRetryFlow.task, status=STATUS.DONE)

        process = TestCeleryProcess.objects.get(pk=activation.process.pk)
        self.assertEqual(STATUS.DONE, process.status)


class TestCeleryProcess(Process):
    throw_error = models.BooleanField(default=False)

    class Meta:
        app_label = 'tests'


@flow.flow_start_func
def create_test_flow(activation, throw_error=False):
    activation.prepare()
    activation.process.throw_error = throw_error
    activation.done()

    return activation


@celery_app.task
@flow.flow_job
def celery_test_job(activation):
    if activation.process.throw_error:
        raise ValueError('Process raised error')


class TestCeleryFlow(Flow):
    process_class = TestCeleryProcess

    start = flow.StartFunction(create_test_flow).Next(this.task)
    task = celery.Job(celery_test_job).Next(this.end)
    end = flow.End()


@celery_app.task(bind=True, default_retry_delay=1)
@method_decorator(flow.flow_job)
def celery_test_retry_job(self, activation):
    if activation.process.throw_error:
        activation.process.throw_error = False
        activation.process.save()
        self.retry()


class TestCeleryRetryFlow(Flow):
    process_class = TestCeleryProcess

    start = flow.StartFunction(create_test_flow).Next(this.task)
    task = celery.Job(celery_test_retry_job).Next(this.end)
    end = flow.End()
