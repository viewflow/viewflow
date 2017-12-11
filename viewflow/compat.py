"""Django compatibility utils."""
from django.apps import apps


def get_app_package(app_label):
    """Return app package string."""
    app_config = apps.get_app_config(app_label)
    if not app_config:
        return None
    return app_config.module.__name__


def get_containing_app_data(module):
    """Return app label and package string."""
    app_config = apps.get_containing_app_config(module)
    if not app_config:
        return None, None
    return app_config.label, app_config.module.__name__
