"""Viewflow - The Django extension for perfectionists with yesterday’s deadlines."""

# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

from django.conf import settings as django_settings
from .conf import settings
from .this_object import this
from .utils import viewprop, Icon, DEFAULT

__title__ = 'Django-Viewflow'
__version__ = '2.0a2'
__author__ = 'Mikhail Podgurskiy'
__license__ = 'AGPL'
__copyright__ = 'Copyright 2018-2021 Mikhail Podgurskiy'

__all__ = (
    'this', 'viewprop', 'Icon', 'DEFAULT'
)

default_app_config = 'viewflow.apps.ViewflowConfig'

if settings.AUTOREGISTER:
    # Register site middleware
    site_middleware = 'viewflow.middleware.SiteMiddleware'
    if site_middleware not in django_settings.MIDDLEWARE:
        django_settings.MIDDLEWARE += (site_middleware, )
    turbo_middleware = 'viewflow.middleware.HotwireTurboMiddleware'
    if turbo_middleware not in django_settings.MIDDLEWARE:
        django_settings.MIDDLEWARE += (turbo_middleware, )
