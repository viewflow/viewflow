from django.db import models
from viewflow.models import Process, Task


class HelloWorldProcess(Process):
    text = models.CharField(max_length=50)
    approved = models.BooleanField(default=False)


class HelloWorldTask(Task):
    class Meta:
        proxy = True
