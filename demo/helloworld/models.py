import jsonstore
from viewflow.models import Process
from viewflow.compat import _


class HelloWorldProcess(Process):
    text = jsonstore.CharField(_('Message'), max_length=50)
    approved = jsonstore.BooleanField(_('Approved'), default=False)

    class Meta:
        proxy = True
        verbose_name = _("World Request")
        verbose_name_plural = _('World Requests')
