from django.db import models
from viewflow.models import Process, Task


class HelloWorldProcess(Process):
    text = models.CharField(max_length=50)
    approved = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Hello world process list'
        permissions = [
            ('can_start_request', 'Can start hello world request'),
            ('can_approve_request', 'Can approve hello world request')
        ]


class HelloWorldTask(Task):
    class Meta:
        proxy = True
