"""Class based CRUD."""

from .base import BaseViewset, IndexViewMixin, Viewset, ViewsetMeta, route
from .sites import AppMenuMixin, Application, Site
from .model import (
    BaseModelViewset,
    DeleteViewMixin,
    DetailViewMixin,
    CreateViewMixin,
    UpdateViewMixin,
    ListBulkActionsMixin,
    ModelViewset,
    ReadonlyModelViewset,
)


__all__ = (
    "BaseViewset",
    "IndexViewMixin",
    "Viewset",
    "ViewsetMeta",
    "route",
    "AppMenuMixin",
    "Application",
    "Site",
    "BaseModelViewset",
    "DeleteViewMixin",
    "DetailViewMixin",
    "CreateViewMixin",
    "UpdateViewMixin",
    "ListBulkActionsMixin",
    "ModelViewset",
    "ReadonlyModelViewset",
)


def current_viewset_reverse(request, viewset, view_name, args=None, kwargs=None):
    """
    Reverse a URL within the current viewset. This function is specifically
    designed for use in templates that belong to a view within a viewset.
    """
    current_app = getattr(request, "current_app", None)
    if current_app is None:
        current_app = getattr(request.resolver_match, "namespace", None)

    if args:
        current_viewset = viewset
        while current_viewset is not None:
            for kwarg in current_viewset.extra_kwargs or []:
                args = [request.resolver_match.kwargs[kwarg]] + args
            current_viewset = current_viewset.parent
    else:
        if kwargs is None:
            kwargs = {}

        current_viewset = viewset
        while current_viewset is not None:
            for kwarg in current_viewset.extra_kwargs or []:
                kwargs.setdefault(kwarg, request.resolver_match.kwargs[kwarg])
            current_viewset = current_viewset.parent

    return viewset.reverse(view_name, args=args, kwargs=kwargs, current_app=current_app)
