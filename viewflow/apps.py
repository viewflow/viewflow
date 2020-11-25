from django.apps import AppConfig


class ViewflowConfig(AppConfig):
    """Default application config."""

    name = 'viewflow'
    label = 'viewflow_base'  # allow to user 'viewflow' label for 'viewflow.workflow'
