from django.db import models
from viewflow.models import Process


class HelloWorldProcess(Process):
    text = models.CharField(max_length=50)
    approved = models.BooleanField(default=False)

    class Meta:
        permissions = [
            ('can_start_request', 'Can start hello world request'),
            ('can_approve_request', 'Can approve hello world request')
        ]
