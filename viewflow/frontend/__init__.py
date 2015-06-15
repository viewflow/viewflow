default_app_config = 'viewflow.frontend.apps.ViewflowFrontendConfig'  # NOQA


def register(flow_class, viewset_class=None):
    from django.apps import apps
    apps.get_app_config('viewflow_frontend').register(flow_class, viewset_class=viewset_class)
    return flow_class
