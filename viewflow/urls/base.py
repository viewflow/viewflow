# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.
import copy
import types
import warnings
from collections import namedtuple, OrderedDict
from typing import Optional, Dict, Any, List
from django.views.generic import RedirectView
from django.urls import ResolverMatch, URLPattern, URLResolver, include, path, reverse
from django.urls.resolvers import RoutePattern

from viewflow.utils import (
    camel_case_to_underscore,
    strip_suffixes,
    list_path_components,
    DEFAULT,
)


class _UrlName(str):
    """
    Dump str wrapper.

    Just to keep a reference over django url resolve calling
    hierarchy.
    """

    def __init__(self, value) -> None:
        str.__init__(value)
        self.extra = {}


class _URLResolver(URLResolver):
    def __init__(self, *args, **kwargs) -> None:
        self.extra = kwargs.pop("extra", {})
        super(_URLResolver, self).__init__(*args, **kwargs)

    def resolve(self, *args, **kwargs) -> ResolverMatch:
        result = super(_URLResolver, self).resolve(*args, **kwargs)
        if not isinstance(result.url_name, _UrlName):
            result.url_name = _UrlName(result.url_name)

        extra = {}
        extra.update(self.extra)
        extra.update(result.url_name.extra)
        result.url_name.extra = extra
        return result


Route = namedtuple("Route", ["prefix", "viewset"])


def route(prefix, viewset: "BaseViewset") -> Route:
    """A viewset url"""
    if not isinstance(viewset, BaseViewset):
        raise ValueError(
            "route(...) second argument should be a viewset instance, got {} instead".format(
                viewset
            )
        )
    return Route(prefix, viewset)


class BaseViewset:
    """
    Base class for defining a class-based Django routing configuration.

    Attributes:
        app_name (Optional[str]): The name of the application associated with this viewset.
        namespace (Optional[str]): The namespace for the URLs of this viewset.
        parent_namespace (Optional[str]): The namespace of the parent viewset.
        extra_kwargs (Optional[Dict[str, Any]]): Additional keyword arguments for URL configuration.
    """

    app_name: Optional[str] = None
    namespace: Optional[str] = None
    parent_namespace: Optional[str] = None
    extra_kwargs: Optional[Dict[str, Any]] = None

    def __init__(self) -> None:
        super().__init__()
        self._parent: Optional[BaseViewset] = None

    @property
    def parent(self) -> Optional["BaseViewset"]:
        """
        Get the parent viewset.

        Returns:
            Optional[BaseViewset]: The parent viewset, if any.
        """
        return self._parent

    @parent.setter
    def parent(self, value: "BaseViewset") -> None:
        """
        Set the parent viewset. This can only be set once.

        Args:
            value (BaseViewset): The viewset to set as the parent.

        Raises:
            Warning: If the parent is being set more than once or if the viewset
                     already has an explicit parent namespace.
        """
        if self._parent is not None:
            warnings.warn(
                f"Viewset {self.__class__.__name__} parent could be set only once",
                Warning,
            )
        if self.parent_namespace is not None:
            warnings.warn(
                f"Viewset {self.__class__.__name__} already has explicit parent namespace",
                Warning,
            )
        self._parent = value

    @property
    def urls(self) -> List[Any]:
        raise NotImplementedError("Subclass should override this")

    def reverse(
        self,
        viewname: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        current_app: Optional[str] = None,
    ) -> str:
        """
        Get the URL for a given viewname, including the namespace.

        Args:
            viewname (str): The name of the view.
            args (Optional[List[Any]], optional): Positional arguments for the view.
            kwargs (Optional[Dict[str, Any]], optional): Keyword arguments for the view.
            current_app (Optional[str], optional): The current application namespace.

        Returns:
            str: The URL for the view with the appropriate namespace
        """
        view_namespace = ""

        current_viewset = self
        while current_viewset:
            namespace = current_viewset.namespace or current_viewset.app_name
            if namespace:
                view_namespace = "{}:{}".format(namespace, view_namespace)
            if current_viewset.parent is None and current_viewset.parent_namespace:
                view_namespace = "{}:{}".format(
                    current_viewset.parent_namespace, view_namespace
                )
            current_viewset = current_viewset.parent

        if view_namespace:
            viewname = view_namespace + viewname

        return reverse(viewname, args=args, kwargs=kwargs, current_app=current_app)

    def has_view_permission(self, user: Any, obj: Optional[Any] = None):
        """
        Determine if the user has permission to view the viewset.

        Args:
            user (User): The user to check permissions for.
            obj (Optional[Any], optional): The object being viewed.

        Returns:
            bool: True if the user has view permission, False otherwise.
        """
        return True


class ViewsetMeta(type):
    """Collect urls declared on the based classes."""

    def __new__(mcs, name, bases, attrs):
        current_patterns = []
        for key, value in list(attrs.items()):
            if not key.endswith("_path") or key.startswith("get_"):
                continue
            current_patterns.append((key, value))

        attrs["declared_patterns"] = OrderedDict()  # current_patterns removed

        new_class = super().__new__(mcs, name, bases, attrs)

        # Walk through the MRO.
        declared_patterns = OrderedDict()
        for base in reversed(new_class.__mro__):
            # Collect fields from base class.
            if hasattr(base, "declared_patterns"):
                declared_patterns.update(base.declared_patterns)

            # Field shadowing.
            for attr, value in base.__dict__.items():
                if value is None and attr in declared_patterns:
                    declared_patterns.pop(attr)

        # place current class items on top of inherited, to allow override first index view in a child class
        # new_class.declared_patterns = declared_patterns
        new_class.declared_patterns = OrderedDict(current_patterns)
        new_class.declared_patterns.update(
            {
                key: value
                for key, value in declared_patterns.items()
                if key not in current_patterns
            }
        )

        return new_class


class Viewset(BaseViewset, metaclass=ViewsetMeta):
    """
    Declarative, class-based django routing configuration

    An Viewset class automatically collect URL patterns from class attributes
    with names ends on `_url` and includes nested Viewset classes from
    attributes with names ends on '_urls'.

    Viewset classes could be inherited, extended, and have overridden attributes.
    """

    viewsets = None
    turbo_disabled = False
    urlpatterns = None

    def __init__(self, **initkwargs):
        super().__init__()
        self._urls_cache = None
        self._children = []

        # customize instance attributes
        for key, value in initkwargs.items():
            if key.startswith("_"):
                raise TypeError(
                    "You tried to pass the private {} name as a "
                    "keyword argument to {}(). Don't do that.".format(
                        key, self.__name__
                    )
                )
            if not hasattr(self.__class__, key):
                raise TypeError(
                    "{}() received an invalid keyword {}. Viewset constructor "
                    "only accepts arguments that are already "
                    "attributes of the class.".format(self.__class__.__name__, key)
                )
            setattr(self, key, value)

        # clone additional routes
        if self.viewsets:
            self.viewsets = [copy.copy(viewset) for viewset in self.viewsets]
            self._children += self.viewsets

        # clone route instances
        for attr_name in self.declared_patterns:
            attr_value = getattr(self.__class__, attr_name)
            if isinstance(attr_value, Route):
                viewset = copy.copy(attr_value.viewset)
                viewset.extra_kwargs = list_path_components(attr_value.prefix)
                setattr(self, attr_name, Route(attr_value.prefix, viewset))
                self._children.append(viewset)

    def _create_url_pattern(self, value):
        if isinstance(value, (URLPattern, URLResolver)):
            return value
        elif isinstance(value, Route):
            value.viewset.parent = self
            patterns, app_name, namespace = value.viewset.urls
            pattern = path(
                value.prefix if value.prefix else "",
                include((patterns, app_name), namespace=namespace),
            )
            return pattern
        else:
            raise ValueError(
                "{} got unknown url entry {}".format(self.__class__.__name__, value)
            )

    def _get_urls(self):
        """
        Collect URLs from the instance attributes.
        """
        urlpatterns = []

        # url overrides
        for url_entry in self.urlpatterns or []:
            urlpatterns.append(self._create_url_pattern(url_entry))

        # class attributes
        for attr_name in self.declared_patterns:
            attr_value = getattr(self, attr_name)
            if isinstance(attr_value, types.FunctionType) or attr_value is None:
                continue
            urlpatterns.append(self._create_url_pattern(attr_value))

        # additional routes
        for viewset in self.viewsets or []:
            if viewset.app_name is None:
                viewset.app_name = camel_case_to_underscore(
                    strip_suffixes(
                        viewset.__class__.__name__,
                        ["App", "Application", "Viewset", "Admin", "Flow"],
                    )
                )
                assert viewset.app_name, "Can't provide auto name for a {}".format(
                    viewset
                )
            urlpatterns.append(
                self._create_url_pattern(route(f"{viewset.app_name}/", viewset))
            )

        return urlpatterns

    def _get_resolver_extra(self):
        return {"viewset": self}

    def filter_kwargs(self, view_class, **kwargs):
        return {
            name: value
            for name, value in kwargs.items()
            if hasattr(view_class, name)
            if value is not DEFAULT
        }

    @property
    def urls(self):
        namespace = self.namespace
        if namespace is None:
            namespace = self.app_name
        if self._urls_cache is None:
            self._urls_cache = self._get_urls()

        pattern = RoutePattern("", is_endpoint=False)
        resolver = _URLResolver(
            pattern, self._urls_cache, extra=self._get_resolver_extra()
        )
        return [resolver], self.app_name, namespace


def _get_index_redirect_url(viewset):
    """
    Return first non-parameterized viewset url.
    """

    def _get_index_url(url_patterns, prefix="./"):
        index_first_patterns = sorted(
            url_patterns, key=lambda pat: getattr(pat, "name", "") != "index"
        )
        for url_pattern in index_first_patterns:
            if isinstance(url_pattern, URLPattern):
                couldbe_index_view = (
                    isinstance(url_pattern.pattern, RoutePattern)
                    and url_pattern.pattern.converters == {}
                    and not (
                        hasattr(url_pattern.callback, "view_class")
                        and url_pattern.callback.view_class == _IndexRedirectView
                    )
                )
                if couldbe_index_view:
                    return prefix + url_pattern.pattern._route
            elif isinstance(url_pattern, URLResolver) and isinstance(
                url_pattern.pattern, RoutePattern
            ):
                return _get_index_url(
                    url_pattern.url_patterns, prefix + url_pattern.pattern._route
                )

    return _get_index_url(viewset.urls[0], "./")


class _IndexRedirectView(RedirectView):
    viewset = None

    def get_redirect_url(self, *args, **kwargs):
        if self.viewset:
            redirect = _get_index_redirect_url(self.viewset)
            if redirect is None:
                raise ValueError(
                    "Can't determine index url. Please add an explicit "
                    "`index_path = path('', RedirectView(url='...'), name='index')`"
                    " declaration for the viewset"
                )
            return redirect
        return super().get_redirect_url(*args, **kwargs)


class IndexViewMixin(metaclass=ViewsetMeta):
    """
    Redirect from / to the first non-parameterized view of the Viewset class.
    """

    @property
    def index_path(self):
        return path("", _IndexRedirectView.as_view(viewset=self), name="index")
