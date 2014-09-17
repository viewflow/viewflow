"""
Import flows before auth permission setup
"""
try:
    from django.db.models.signals import pre_migrate

    def import_flows(app_config, **kwargs):
        """
        Pre-import flows to allow permissions auto-creation
        """
        try:
            __import__('{}.flows'.format(app_config.module.__name__))
        except ImportError:
            pass

    pre_migrate.connect(import_flows, dispatch_uid="viewflow.management.import_flows")

except ImportError:
    # django 1.6
    try:
        from south.signals import pre_migrate, post_migrate
        from ..compat import get_app_package

        def import_flows(app, **kwargs):
            try:
                __import__('{}.flows'.format(get_app_package(app)))
            except ImportError:
                pass

        pre_migrate.connect(import_flows, dispatch_uid="viewflow.management.import_flows")

        from django.conf import settings
        if 'django.contrib.auth' in settings.INSTALLED_APPS:
            def create_permissions_compat(app, **kwargs):
                from django.db.models import get_app
                from django.contrib.auth.management import create_permissions
                create_permissions(get_app(app), (), 0)
            post_migrate.connect(create_permissions_compat)

    except ImportError:
        from django.db.models.signals import pre_syncdb

        def import_flows(sender, **kwargs):
            """
            Pre-import flows to allow permissions auto-creation
            """
            try:
                __import__('{}.flows'.format(sender.__package__))
            except ImportError:
                pass

        pre_syncdb.connect(import_flows, dispatch_uid="viewflow.management.import_flows")
