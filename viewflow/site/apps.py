from django.apps import AppConfig


class ViewSiteConfig(AppConfig):
    """
    Default AppConfig for viewsite which does autodiscovery
    """
    name = 'viewflow.site'
    viebose_name = 'Viewflow Site'

    def ready(self):
        super(ViewSiteConfig, self).ready()
        self.module.autodiscover()
