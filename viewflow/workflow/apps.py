from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class WorkflowConfig(AppConfig):
    """Default application config."""

    name = 'viewflow.workflow'
    label = 'viewflow'  # keep backward compatible with 1.x
    verbose_name = _('Workflow')
