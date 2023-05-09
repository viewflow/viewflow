# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

import re
from typing import Any, Callable, Iterator, List, Optional, Tuple, Type, TypeVar

from django.apps import apps
from django.conf import settings
from django.contrib import auth
from django.core import mail
from django.db import models
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

__all__ = ("has_object_perm", "viewprop", "DEFAULT", "first_not_default")


T = TypeVar("T")
TCallable = TypeVar("TCallable", bound=Callable[..., Any])


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
    if not args:
        return None

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
    perm_name = f"{model._meta.app_label}.{auth.get_permission_codename(short_perm_name, model._meta)}"
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


def is_owner(owner: models.Model, user: models.Model) -> bool:
    """
    Checks whether the specified user instance or subclass is equal to the
    specified owner instance or subclass.
    """
    return isinstance(user, type(owner)) and owner.pk == user.pk


class viewprop:
    """
    A property that can be overridden.

    The viewprop class is a descriptor that works similarly to the built-in
    `property` decorator but allows its value to be overridden on instances
    of the class it is used in.
    """

    def __init__(self, func: Any):
        self.__doc__ = getattr(func, "__doc__")
        self.fget = func

    def __get__(self, obj: Optional[Any], objtype: Optional[Type[Any]] = None) -> Any:
        if obj is None:
            return self
        if self.fget.__name__ not in obj.__dict__:
            obj.__dict__[self.fget.__name__] = self.fget(obj)
        return obj.__dict__[self.fget.__name__]

    def __set__(self, obj: Any, value: Any) -> None:
        obj.__dict__[self.fget.__name__] = value

    def __repr__(self) -> str:
        return "<view_property func={}>".format(self.fget)


class LazySingletonDescriptor:
    """
    Descriptor class that creates a lazy singleton instance.

    This descriptor can be used as a class attribute, and the first time the
    attribute is accessed, it creates an instance of the class. Subsequent
    accesses return the same instance, effectively making the class a singleton.
    """

    def __init__(self) -> None:  # noqa D102
        self.instance: Optional[T] = None

    def __get__(
        self,
        instance: Optional[T] = None,
        owner: Optional[Type[T]] = None,
    ) -> T:
        if self.instance is None:
            if owner is None:
                raise ValueError("Owner class not provided")
            self.instance = owner()
        return self.instance


class Icon:
    """
    Class representing an HTML icon element.

    Attributes:
    -----------
    icon_name : str
        The name of the icon to use.
    class_ : str, optional
        The CSS class to apply to the icon element.
    """

    def __init__(self, icon_name: str, class_: Optional[str] = None):
        self.icon_name = icon_name
        self.class_ = class_ or ""

    def __str__(self) -> str:
        icon_name = conditional_escape(self.icon_name)
        class_name = conditional_escape(self.class_)
        return mark_safe(
            f'<i class="material-icons ${class_name}" aria-hidden="true">{icon_name}</i>'
        )


def get_object_data(obj: models.Model) -> Iterator[Tuple[models.Field, str, Any]]:
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


PATH_PARAMETER_COMPONENT_RE = re.compile(
    r"<(?:(?P<converter>[^>:]+):)?(?P<parameter>[^>]+)>"
)


def list_path_components(route: str) -> List[str]:
    """
    Extract keyword arguments from a Django path expression, which are used as
    input parameters for a view function.

    Example Usage:

     >>> list_path_components('/prefix/<str:pk>')
     ['pk']
     >>> list_path_components('<str:pk>/<int:id>')
     ['pk', 'id']
    """
    return [match["parameter"] for match in PATH_PARAMETER_COMPONENT_RE.finditer(route)]
