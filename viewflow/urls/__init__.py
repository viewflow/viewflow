"""Class based CRUD."""

from .base import (
    BaseViewset, IndexViewMixin, Viewset, ViewsetMeta, route
)
from .sites import AppMenuMixin, Application, Site
from .model import (
    BaseModelViewset, DeleteViewMixin, DetailViewMixin, CreateViewMixin,
    UpdateViewMixin, ListBulkActionsMixin, ModelViewset, ReadonlyModelViewset,
)


__all__ = (
    'BaseViewset', 'IndexViewMixin', 'Viewset', 'ViewsetMeta', 'route',
    'AppMenuMixin', 'Application', 'Site',
    'BaseModelViewset', 'DeleteViewMixin', 'DetailViewMixin', 'CreateViewMixin',
    'UpdateViewMixin', 'ListBulkActionsMixin', 'ModelViewset', 'ReadonlyModelViewset',
)
