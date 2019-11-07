"""Import flows before auth permission setup."""
from __future__ import unicode_literals

import django
from django.apps import apps
from django.db import DEFAULT_DB_ALIAS, router
from django.db.models.signals import pre_migrate, post_migrate
from django.utils.encoding import smart_text


def create_permissions(app_config, verbosity=2, interactive=True, using=DEFAULT_DB_ALIAS, **kwargs):
    """Create permissions on django 1.10+."""
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
        # ctype = ContentType.objects.db_manager(using).get_for_model(klass)
        opts = klass._meta
        ctype, _ = ContentType.objects.get_or_create(
                app_label=opts.app_label,
                model=opts.object_name.lower()
        )
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
