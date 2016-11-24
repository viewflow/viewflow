from django.db import models
from django.conf import settings
from viewflow.models import Process


class DynamicSplitProcess(Process):
    question = models.CharField(max_length=50)
    split_count = models.IntegerField(default=0)


class Decision(models.Model):
    process = models.ForeignKey(DynamicSplitProcess, on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE)
    decision = models.BooleanField(default=False)
