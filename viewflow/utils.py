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
    """
    Return the first argument that is not the `DEFAULT` marker. If all arguments
    are `DEFAULT`, return the last one.
    """
    for arg in args:
        if arg is not DEFAULT:
            return arg
    return arg


def camel_case_to_underscore(name):
    """
    Convert a camel-cased string to an underscore-separated string.
    For example, 'SomeString' becomes 'some_string'.
    """

    return re.sub(
        "([a-z0-9])([A-Z])", r"\1_\2", re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    ).lower()


def camel_case_to_title(name):
    """
    Convert a camel-cased string to a title-cased string.
    For example, 'SomeString' becomes 'Some String'.
    """

    return re.sub(
        "([a-z0-9])([A-Z])", r"\1 \2", re.sub("(.)([A-Z][a-z]+)", r"\1 \2", name)
    ).capitalize()


def has_object_perm(user, short_perm_name, model, obj=None):
    """
    Check if the user has the specified permission for the given model. If an
    object is provided, and user has no model-wide permission, check if the user
    has the permission for that specific object instance.
    """
    perm_name = auth.get_permission_codename(short_perm_name, model._meta)
    has_perm = user.has_perm(perm_name)
    if not has_perm and obj is not None:
        has_perm = user.has_perm(perm_name, obj=obj)
    return has_perm


def strip_suffixes(word, suffixes):
    """
    Strip the specified suffixes from the given word.
    Never strip the whole word to an empty string.
    """

    for suffix in suffixes:
        if word != suffix and word.endswith(suffix):
            word = word[: -len(suffix)]
    return word


def strip_dict_keys_prefix(a_dict, prefix):
    """
    Construct a new dictionary from the keys of the provided dictionary that
    start with the specified prefix.
    """

    return {
        key[len(prefix) :]: value
        for key, value in a_dict.items()
        if key.startswith(prefix)
    }


def get_app_package(app_label):
    """
    Returns the name of the package that contains the specified app or None if
    the app is not found.
    """
    app_config = apps.get_app_config(app_label)
    if not app_config:
        return None
    return app_config.module.__name__


def get_containing_app_data(module):
    """
    Returns the app label and package string for the specified module.
    """
    app_config = apps.get_containing_app_config(module)
    if not app_config:
        return None, None
    return app_config.label, app_config.module.__name__


def is_owner(owner, user):
    """
    Checks whether the specified user instance or subclass is equal to the
    specified owner instance or subclass.
    """
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


class LazySingletonDescriptor(object):
    """
    Descriptor class that creates a lazy singleton instance.
    """

    def __init__(self):  # noqa D102
        self.instance = None

    def __get__(self, instance=None, owner=None):
        if self.instance is None:
            self.instance = owner()
        return self.instance


class Icon(object):
    """
    Class representing an HTML icon element.

    Attributes:
    -----------
    icon_name : str
        The name of the icon to use.
    class_ : str, optional
        The CSS class to apply to the icon element.
    """

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
    """
    List of object fields to display. Choice fields values are expanded to
    readable choice label.

    Returns a list of (field, label, value) tuples for the fields of the given
    object.

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

    if hasattr(obj, "artifact_object_id") and obj.artifact_object_id:
        yield from get_object_data(obj.artifact)
