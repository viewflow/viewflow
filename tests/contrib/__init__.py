import os
import signal
import subprocess
import sys
import time
import unittest

from django.db import connection
from django.test import TransactionTestCase

from viewflow.workflow.models import Task


@unittest.skipUnless(
    "DATABASE_URL" in os.environ, "Celery test requires specific database config"
)
class CeleryTestCase(TransactionTestCase):
    SETTINGS = "cookbook.workflow101.config"

    def setUp(self):
        """Start celery worker connection the the test database"""
        env = os.environ.copy()
        database_url = env["DATABASE_URL"]
        env["DATABASE_URL"] = "{}/{}".format(
            database_url[: database_url.rfind("/")], connection.settings_dict["NAME"]
        )

        cmd = [
            "celery",
            "--app",
            self.SETTINGS,
            "worker",
            "--loglevel",
            "DEBUG",
            "-E",
            "-c",
            "1",
        ]
        self.process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )
        self.assertIsNone(self.process.poll())

    def tearDown(self):
        self.process.send_signal(signal.SIGTERM)
        if "-v3" in sys.argv:
            stdout, stderr = self.process.communicate()
            print(" CELERY STDOUT ".center(80, "="))
            print(stdout.decode())

            print(" CELERY STDERR ".center(80, "="), file=sys.stderr)
            print(stderr.decode(), file=sys.stderr)

    def wait_for_task(self, process, flow_task, status=None):
        for _ in range(100):
            try:
                return process.task_set.filter(flow_task=flow_task, status=status).get()
            except Task.DoesNotExist:
                time.sleep(0.05)
        assert False, "Task {} not found".format(flow_task)
