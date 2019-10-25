"""Django compatibility utils."""
import django
from django.apps import apps


__all__ = ('_', 'get_app_package', 'get_containing_app_data')


if django.VERSION >= (3, 0):
    from django.utils.translation import gettext_lazy as _
else:
    from django.utils.translation import ugettext_lazy as _


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
