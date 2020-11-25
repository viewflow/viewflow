"""Viewflow - dev toolkit for backoffice automation."""
from django.conf import settings as django_settings
from .conf import settings
from .this_object import this
from .utils import viewprop, Icon, DEFAULT

__title__ = 'Django-Viewflow'
__version__ = '2.0a1'
__author__ = 'Mikhail Podgurskiy'
__license__ = 'AGPL'
__copyright__ = 'Copyright 2018 Mikhail Podgurskiy'

__all__ = (
    'this', 'viewprop', 'Icon', 'DEFAULT'
)

default_app_config = 'viewflow.apps.ViewflowConfig'

if settings.AUTOREGISTER:
    # Register site middleware
    site_middleware = 'viewflow.middleware.SiteMiddleware'
    if site_middleware not in django_settings.MIDDLEWARE:
        django_settings.MIDDLEWARE += (site_middleware, )
    turbolinks_middleware = 'viewflow.middleware.TurbolinksMiddleware'
    if turbolinks_middleware not in django_settings.MIDDLEWARE:
        django_settings.MIDDLEWARE += (turbolinks_middleware, )
