import warnings

from ..base import ThisObject, This, Edge, Node, Event, Task, Gateway
from ..mixins import (
    NextNodeMixin, DetailsViewMixin, UndoViewMixin, CancelViewMixin,
    PerformViewMixin, ActivateNextMixin, PermissionMixin, TaskDescriptionMixin,
    TaskDescriptionViewMixin, ViewArgsMixin
)


__all__ = [
    'ThisObject', 'This', 'Edge', 'Node', 'Event', 'Task', 'Gateway',
    'NextNodeMixin', 'DetailsViewMixin', 'UndoViewMixin', 'CancelViewMixin',
    'PerformViewMixin', 'ActivateNextMixin', 'PermissionMixin', 'TaskDescriptionMixin',
    'TaskDescriptionViewMixin', 'ViewArgsMixin'
]


warnings.warn(
    "Importing from viewflow.flow.base is deprecated in favor of viewflow.base and viewflow.mixins",
    DeprecationWarning, stacklevel=2)
