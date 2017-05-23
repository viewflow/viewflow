from django.db import models
from viewflow.models import Process, Task
from django.utils.translation import ugettext_lazy as _


class HelloWorldProcess(Process):
    text = models.CharField(_('Message'), max_length=50)
    approved = models.BooleanField(_('Approved'), default=False)

    class Meta:
        verbose_name = _("World Request")
        verbose_name_plural = _('World Requests')
