"""Import flows before auth permission setup."""

try:
    import django
    from django.apps import apps
    from django.db import DEFAULT_DB_ALIAS, router
    from django.db.models.signals import pre_migrate, post_migrate

    def create_permissions(app_config, verbosity=2, interactive=True, using=DEFAULT_DB_ALIAS, **kwargs):
        """Create permissions on django 1.10+ """
        if not app_config.models_module:
            return

        try:
            ContentType = apps.get_model('contenttypes', 'ContentType')
            Permission = apps.get_model('auth', 'Permission')
        except LookupError:
            return

        if not router.allow_migrate_model(using, Permission):
            return

        searched_perms = list()  # (content_type, (codename, name))
        ctypes = set()           # The codenames and ctypes that should exist.

        for klass in app_config.get_models():
            ctype = ContentType.objects.db_manager(using).get_for_model(klass)
            ctypes.add(ctype)

            from django.contrib.auth.management import _get_all_permissions
            for perm in _get_all_permissions(klass._meta):
                searched_perms.append((ctype, perm))

        all_perms = set(Permission.objects.using(using).filter(
            content_type__in=ctypes,
        ).values_list(
            "content_type", "codename"
        ))

        perms = [
            Permission(codename=codename, name=name, content_type=ct)
            for ct, (codename, name) in searched_perms
            if (ct.pk, codename) not in all_perms
        ]

        Permission.objects.using(using).bulk_create(perms)
        if verbosity >= 2:
            for perm in perms:
                print("Adding permission '%s'" % perm)

    def import_flows(app_config, **kwargs):
        """Pre-import flows to allow permissions auto-creation."""
        try:
            __import__('{}.flows'.format(app_config.module.__name__))
        except ImportError:
            pass

    pre_migrate.connect(import_flows, dispatch_uid="viewflow.management.import_flows")
    if django.VERSION >= (1, 10):
        post_migrate.connect(create_permissions, dispatch_uid="viewflow.management.create_permissions")

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
            """Pre-import flows to allow permissions auto-creation."""
            try:
                __import__('{}.flows'.format(sender.__package__))
            except ImportError:
                pass

        pre_syncdb.connect(import_flows, dispatch_uid="viewflow.management.import_flows")
