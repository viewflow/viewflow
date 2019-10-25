from django.db import models
from viewflow.models import Process
from viewflow.compat import _


class HelloWorldProcess(Process):
    text = models.CharField(_('Message'), max_length=50)
    approved = models.BooleanField(_('Approved'), default=False)

    class Meta:
        verbose_name = _("World Request")
        verbose_name_plural = _('World Requests')
