"""Import flows before auth permission setup."""

# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial licence defined in file 'COMM_LICENSE',
# which is part of this source code package.

import os
import warnings

from django.apps import apps
from django.db import DEFAULT_DB_ALIAS, router
from django.db.models.signals import pre_migrate, post_migrate


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
    except ImportError as err:
        if os.path.exists(os.path.join(app_config.path, 'flows.py')):
            warnings.warn(
                f"'{err}' during import flows.py for {app_config.name}\n\n"
                "Flow nodes custom permissions might not autocreated",
                stacklevel=2
            )


pre_migrate.connect(import_flows, dispatch_uid="viewflow.management.import_flows")
post_migrate.connect(create_permissions, dispatch_uid="viewflow.management.create_permissions")
