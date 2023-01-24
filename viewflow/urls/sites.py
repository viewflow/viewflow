# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

from django.urls import NoReverseMatch
from django.utils.functional import cached_property

from viewflow.utils import Icon, camel_case_to_title, strip_suffixes

from .base import IndexViewMixin, Viewset


class AppMenuMixin:
    """A route that can be listed in an Application menu."""

    title = None
    icon = Icon("view_carousel")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if isinstance(self.icon, str):
            self.icon = Icon(self.icon)

    def __getattribute__(self, name):
        attr = super().__getattribute__(name)

        if name == "title" and attr is None:
            class_title = camel_case_to_title(
                strip_suffixes(
                    self.__class__.__name__, ["Viewset", "Admin", "App", "Flow"]
                )
            )
            if not class_title:
                raise ValueError("Application item needs a title")
            return class_title + "s"

        return attr

    def has_view_permission(self, user, obj=None):
        if hasattr(super(), "has_view_permission"):
            return super().has_view_permission(user, obj=obj)
        return True


class Application(IndexViewMixin, Viewset):
    title = ""
    icon = Icon("view_module")
    menu_template_name = "viewflow/includes/app_menu.html"
    base_template_name = "viewflow/base_page.html"
    permission = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if isinstance(self.icon, str):
            self.icon = Icon(self.icon)

    def __getattribute__(self, name):
        attr = super().__getattribute__(name)

        if name == "title" and attr is not None and not attr:
            title = camel_case_to_title(
                strip_suffixes(
                    self.__class__.__name__,
                    ["Application", "Viewset", "Admin", "App", "Flow"],
                )
            )
            if not title:
                raise ValueError("Application needs a title")
            return title

        return attr

    def _get_resolver_extra(self):
        return {"viewset": self, "app": self}

    def get_context_data(self, request):
        return {}

    def has_view_permission(self, user, obj=None):
        if self.permission is not None:
            if callable(self.permission):
                return self.permission(user)
            return user.is_authenticated and user.has_perm(self.permission)
        return True

    def menu_items(self):
        for viewset in self._children:
            if isinstance(viewset, AppMenuMixin):
                yield viewset


class Site(IndexViewMixin, Viewset):
    title = None
    icon = Icon("view_comfy")
    menu_template_name = "viewflow/includes/site_menu.html"
    primary_color = None
    secondary_color = None
    permission = None

    def __init__(self, *, title=None, **kwargs):
        super().__init__(**kwargs)

        if isinstance(self.icon, str):
            self.icon = Icon(self.icon)

        if title is not None:
            self.title = title

        if self.title is None:
            # pluralize class name
            self.title = camel_case_to_title(
                strip_suffixes(self.__class__.__name__, ["Site"])
            )
            if not self.title:
                self.title = "Django Viewflow"

    def __getattribute__(self, name):
        attr = super().__getattribute__(name)

        if name == "title" and attr is None:
            title = camel_case_to_title(
                strip_suffixes(self.__class__.__name__, ["Site"])
            )
            if not title:
                title = "Django Viewflow"
            return title

        return attr

    def _get_resolver_extra(self):
        return {"viewset": self, "site": self}

    def menu_items(self):
        for viewset in self._children:
            if isinstance(viewset, (Site, Application)):
                yield viewset

    def has_view_permission(self, user, obj=None):
        if self.permission is not None:
            return user.has_perm(self.permission)
        return True

    def register(self, app_class):
        app = app_class()
        app._parent = self
        self.viewsets.append(app)
        return app_class

    @cached_property
    def _viewset_models(self):
        result = {}

        queue = list(self._children)
        while queue:
            viewset = queue.pop(0)
            if (
                hasattr(viewset, "model")
                and hasattr(viewset, "get_object_url")
                and viewset.model not in result
            ):
                result[viewset.model] = viewset
            for child_viewset in viewset._children:
                if isinstance(child_viewset, Viewset):
                    queue.append(child_viewset)
        return result

    def get_absolute_url(self, request, obj):
        model = type(obj)
        if model in self._viewset_models:
            return self._viewset_models[model].get_object_url(request, obj)
        else:
            raise NoReverseMatch("Viewset for {} not found".format(model.__name__))
