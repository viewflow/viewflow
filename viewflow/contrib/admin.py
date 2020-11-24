from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from viewflow import Icon
from viewflow.urls import Application


class Admin(Application):
    """
    Django administration Viewset adapter::

        from material.contrib.admin import Admin

        site = Site(apps=[
            Admin()
        ])

        urls = [
            path('', site.urls)
        ]

    """
    app_name = 'admin'
    namespace = 'admin'
    prefix = 'admin'

    title = _("Administration")
    icon = Icon("build")
    turbolinks_disabled = True

    def __init__(self, *, admin_site=None, **kwargs):
        self.admin_site = admin_site or admin.site
        super().__init__(**kwargs)

    def has_perm(self, user):
        return user.is_staff

    @property
    def urls(self):
        url_patterns, app_name, namespace = self.admin_site.urls
        assert self.app_name == app_name
        assert self.namespace == namespace
        return url_patterns, app_name, namespace
