from django.apps import AppConfig, apps
from django.conf import settings as django_settings

# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial licence defined in file 'COMM_LICENSE',
# which is part of this source code package.


class ViewflowConfig(AppConfig):
    """Default application config."""

    name = "viewflow"
    label = "viewflow_base"  # allow to user 'viewflow' label for 'viewflow.workflow'

    def ready(self):
        from .conf import settings

        # The registry isn't populated yet when viewflow.conf.DEFAULTS is
        # first computed, so its AUTOREGISTER default is a best-effort
        # string check that only recognizes the bare "viewflow" app-label
        # form. apps.is_installed() is only safe to call here, once every
        # app is loaded, and correctly recognizes viewflow regardless of
        # how it's spelled in INSTALLED_APPS (including the
        # "viewflow.apps.ViewflowConfig" AppConfig-path form). Only
        # correct the default -- an explicit user setting always wins.
        custom = getattr(django_settings, "VIEWFLOW", {})
        if "AUTOREGISTER" not in custom:
            settings.settings["AUTOREGISTER"] = apps.is_installed("viewflow")

        if settings.AUTOREGISTER:
            site_middleware = "viewflow.middleware.SiteMiddleware"
            if site_middleware not in django_settings.MIDDLEWARE:
                django_settings.MIDDLEWARE += (site_middleware,)
            turbo_middleware = "viewflow.middleware.HotwireTurboMiddleware"
            if turbo_middleware not in django_settings.MIDDLEWARE:
                django_settings.MIDDLEWARE += (turbo_middleware,)
