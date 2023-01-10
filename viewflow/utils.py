# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

import re
from functools import update_wrapper

from django.apps import apps
from django.core import mail
from django.conf import settings
from django.contrib import auth
from django.db import models
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

__all__ = ("has_object_perm", "viewprop", "DEFAULT", "first_not_default")


class MARKER(object):
    def __init__(self, marker: str):
        self.marker = marker

    def __iter__(self):
        return iter(())

    def __repr__(self):
        return self.marker


DEFAULT = MARKER("DEFAULT")

IS_DEV = settings.DEBUG or not hasattr(mail, "outbox")  # DEBUG or test mode


def first_not_default(*args):
    for arg in args:
        if arg is not DEFAULT:
            return arg
    return arg


def camel_case_to_underscore(name):
    """Convert camel cased SomeString to some_string"""

    return re.sub(
        "([a-z0-9])([A-Z])", r"\1_\2", re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    ).lower()


def camel_case_to_title(name):
    """Convert camel cased 'SomeString' to 'Some string'"""

    return re.sub(
        "([a-z0-9])([A-Z])", r"\1 \2", re.sub("(.)([A-Z][a-z]+)", r"\1 \2", name)
    ).capitalize()


def has_object_perm(user, short_perm_name, model, obj=None):
    perm_name = auth.get_permission_codename(short_perm_name, model._meta)
    has_perm = user.has_perm(perm_name)
    if not has_perm and obj is not None:
        has_perm = user.has_perm(perm_name, obj=obj)
    return has_perm


def strip_suffixes(word, suffixes):
    """Strip suffixes from the word.

    Never strips whole word to empty string.
    """

    for suffix in suffixes:
        if word != suffix and word.endswith(suffix):
            word = word[: -len(suffix)]
    return word


def strip_dict_keys_prefix(a_dict, prefix):
    """Construct new dict, from source keys started with prefix."""

    return {
        key[len(prefix):]: value
        for key, value in a_dict.items()
        if key.startswith(prefix)
    }


def get_app_package(app_label):
    """Return app package string."""
    app_config = apps.get_app_config(app_label)
    if not app_config:
        return None
    return app_config.module.__name__


def get_containing_app_data(module):
    """Return app label and package string."""
    app_config = apps.get_containing_app_config(module)
    if not app_config:
        return None, None
    return app_config.label, app_config.module.__name__


def is_owner(owner, user):
    """Check user instances and subclasses for equality."""
    return isinstance(user, owner.__class__) and owner.pk == user.pk


class viewprop(object):
    """
    A property that can be overridden.
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, "__doc__")
        self.fget = func

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget.__name__ not in obj.__dict__:
            obj.__dict__[self.fget.__name__] = self.fget(obj)
        return obj.__dict__[self.fget.__name__]

    def __set__(self, obj, value):
        obj.__dict__[self.fget.__name__] = value

    def __repr__(self):
        return "<view_property func={}>".format(self.fget)


def create_wrapper_view(origin_view, flow_task=None, flow_class=None):
    """Create a wrapper view with flow_task/flow_class injected."""

    def view(request, *args, **kwargs):
        if flow_class is not None:
            request.flow_class = flow_class
        if flow_task is not None:
            request.flow_task = flow_task
        return origin_view(request, *args, **kwargs)

    return update_wrapper_view(
        view, origin_view, flow_task=flow_task, flow_class=flow_class
    )


def update_wrapper_view(view, origin_view, flow_task=None, flow_class=None):
    """Update a wrapper view to look like the wrapped origin_view."""

    view_class = None
    if hasattr(origin_view, "view_class"):  # django generic view
        view_class = view.view_class = origin_view.view_class
    if hasattr(origin_view, "cls"):  # django restframework generic view
        view_class = view.cls = origin_view.cls
    # if hasattr(origin_view, "view_initkwargs"):  # both 八(＾□＾*)
    #    view.view_initkwargs = origin_view.initkwargs or {}

        # poor-man dependency injection. Mostly b/c of dumb restframework BaseSchemaGenerator.create_view impl
        if flow_class and hasattr(view_class, "flow_class"):
            view.view_initkwargs["flow_task"] = flow_class
        if flow_task and hasattr(view_class, "flow_task"):
            view.view_initkwargs["flow_task"] = flow_task

    update_wrapper(view, origin_view)
    return view


class LazySingletonDescriptor(object):
    """Descriptor class for lazy singleton instance."""

    def __init__(self):  # noqa D102
        self.instance = None

    def __get__(self, instance=None, owner=None):
        if self.instance is None:
            self.instance = owner()
        return self.instance


class Icon(object):
    def __init__(self, icon_name, class_=None):
        self.icon_name = icon_name
        self.class_ = class_ or ""

    def __str__(self):
        icon_name = conditional_escape(self.icon_name)
        class_name = conditional_escape(self.class_)
        return mark_safe(
            f'<i class="material-icons ${class_name}" aria-hidden="true">{icon_name}</i>'
        )


def get_object_data(obj):
    """List of object fields to display.
    Choice fields values are expanded to readable choice label.
    """
    for field in obj._meta.fields:
        if isinstance(field, models.AutoField):
            continue
        elif field.auto_created:
            continue
        else:
            choice_display_attr = "get_{}_display".format(field.name)
        if hasattr(obj, choice_display_attr):
            value = getattr(obj, choice_display_attr)()
        else:
            value = getattr(obj, field.name)

        if value is not None:
            yield (field, field.verbose_name.capitalize(), value)

    if hasattr(obj, 'artifact_object_id') and obj.artifact_object_id:
        yield from get_object_data(obj.artifact)
