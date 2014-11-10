from __future__ import print_function

import os
import subprocess
import sys
import time

from django.db import models, connection
from django.test import TransactionTestCase

from viewflow import flow
from viewflow.base import Flow, this
from viewflow.contrib import celery
from viewflow.models import Process, Task

from tests import celery_app


class TestCeleryProcess(Process):
    throw_error = models.BooleanField(default=False)

    class Meta:
        app_label = 'integration'


def create_test_flow(activation, throw_error=False):
    activation.prepare()
    activation.process.throw_error = throw_error
    activation.done()

    return activation


@celery_app.task()
@flow.flow_job()
def celery_test_job(activation):
    if activation.process.throw_error:
        raise ValueError('Process raised error')


class TestCeleryFlow(Flow):
    process_cls = TestCeleryProcess

    start = flow.StartFunction(create_test_flow).Next(this.task)
    task = celery.Job(celery_test_job).Next(this.end)
    end = flow.End()


class TestCelery(TransactionTestCase):
    def setUp(self):
        """
        Start celery on the same test database
        """
        env = os.environ.copy()
        if 'DATABASE_URL' in env:
            database_url = env['DATABASE_URL']
            env['DATABASE_URL'] = '{}/{}'.format(database_url[:database_url.rfind('/')],
                                                 connection.settings_dict['NAME'])
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
        for _ in range(5):
            try:
                return process.get_task(flow_task, status=status)
            except Task.DoesNotExist:
                time.sleep(1)
        assert False, 'Task {} not found'.format(flow_task)

    def test_flow_succeed(self):
        activation = TestCeleryFlow.start.run(throw_error=False)

        self.wait_for_task(activation.process, TestCeleryFlow.task, status=[Task.STATUS.FINISHED])

        process = TestCeleryProcess.objects.get(pk=activation.process.pk)
        self.assertEqual(Process.STATUS.FINISHED, process.status)

    def test_flow_failed(self):
        activation = TestCeleryFlow.start.run(throw_error=True)
        self.wait_for_task(activation.process, TestCeleryFlow.task, status=[Task.STATUS.ERROR])
