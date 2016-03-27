import warnings

from .flow.views import ActivateNextView as TaskActivateNextView
from .flow.views import ActivationViewMixin as TaskActivionViewMixin
from .flow.views import AssignView
from .flow.views import CancelView as TaskCancelView
from .flow.views import DetailsView
from .flow.views import PerformView as TaskPerformView
from .flow.views import ProcessView
from .flow.views import StartActivationViewMixin
from .flow.views import StartProcessView
from .flow.views import StartViewMixin
from .flow.views import UnassignView as TaskUnAssignView
from .flow.views import UndoView as TaskUndoView
from .flow.views import ViewMixin as TaskViewMixin
from .flow.views.list import AllArchiveListView
from .flow.views.list import AllProcessListView
from .flow.views.list import AllQueueListView
from .flow.views.list import AllTaskListView
from .flow.views.list import ProcessDetailView
from .flow.views.list import ProcessListView
from .flow.views.list import QueueListView
from .flow.views.list import TaskListView
from .flow.views.process import CancelView as ProcessCancelView


__all__ = [
    'TaskActivateNextView', 'TaskActivionViewMixin', 'AssignView',
    'TaskCancelView', 'DetailsView', 'TaskPerformView', 'ProcessView',
    'StartActivationViewMixin', 'StartProcessView', 'StartViewMixin',
    'TaskUnAssignView', 'TaskUndoView', 'TaskViewMixin',
    'AllArchiveListView', 'AllProcessListView', 'AllQueueListView',
    'AllTaskListView', 'ProcessDetailView', 'ProcessListView',
    'QueueListView', 'TaskListView', 'ProcessCancelView'
]


warnings.warn(
    "Importing from viewflow.views is deprecated in favor of viewflow.flow.views",
    DeprecationWarning, stacklevel=2)
