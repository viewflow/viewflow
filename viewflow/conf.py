"""
Settings for Viewflow are all namespaced in the VIEWFLOW setting.
For example your project's `settings.py` file might look like this:

VIEWFLOW = {
    'WIDGET_RENDERERS': {
        'django.forms.DateTimeInput': 'myapp.renderers.MyDateTimeRenderer'
    }
}
"""

# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial licence defined in file 'COMM_LICENSE',
# which is part of this source code package.


from copy import deepcopy

from django.conf import settings as django_settings
from django.test.signals import setting_changed
from django.utils.module_loading import import_string

from viewflow.forms import renderers


DEFAULTS = {
    'AUTOREGISTER': 'viewflow' in django_settings.INSTALLED_APPS,
    'WIDGET_RENDERERS': renderers.WIDGET_RENDERERS,
}


class Settings(object):
    def __init__(self, custom=None):
        if custom is None:
            custom = getattr(django_settings, 'VIEWFLOW', {})
        self.settings = deepcopy(DEFAULTS)

        for key, value in custom.get('WIDGET_RENDERERS', {}):
            widget_class, renderer_class = import_string(key), import_string(value)
            self.settings['WIDGET_RENDERERS'][widget_class] = renderer_class()

    def __getattr__(self, attr):
        if attr not in self.settings:
            raise AttributeError("Invalid viewflow setting: '%s'" % attr)
        return self.settings[attr]


settings = Settings()


def reload_settings(*args, **kwargs):
    global settings
    setting, value = kwargs['setting'], kwargs['value']
    if setting == 'VIEWFLOW':
        settings = Settings(value)


setting_changed.connect(reload_settings)
