from django.db import models
from viewflow.models import Process


class StepProcess(Process):
    one = models.CharField(max_length=50)
    two = models.CharField(max_length=50)
    three = models.CharField(max_length=50)
