""" Standalone workflow views. """

from .actions import (
    AssignTaskView,
    CancelProcessView,
    BulkUnassignTasksActionView,
    BulkAssignTasksActionView,
)
from .chart import FlowChartView
from .create import CreateProcessView, CreateArtifactView
from .dashboard import DashboardView, DashboardTaskListView, DashboardProcessListView
from .detail import IndexTaskView, UserIndexTaskView, DetailTaskView, DetailProcessView
from .mixins import (
    SuccessMessageMixin,
    TaskSuccessUrlMixin,
    ProcessViewTemplateNames,
    TaskViewTemplateNames,
)
from .update import UpdateProcessView, UpdateArtifactView
from .list import (
    FlowInboxListView,
    FlowQueueListView,
    FlowArchiveListView,
    WorkflowInboxListView,
    WorkflowQueueListView,
    WorkflowArchiveListView,
)


__all__ = (
    "AssignTaskView",
    "BulkAssignTasksActionView",
    "BulkUnassignTasksActionView",
    "CancelProcessView",
    "CreateArtifactView",
    "CreateProcessView",
    "DashboardProcessListView",
    "DashboardTaskListView",
    "DashboardView",
    "DetailProcessView",
    "DetailTaskView",
    "FlowArchiveListView",
    "FlowChartView",
    "FlowInboxListView",
    "FlowQueueListView",
    "IndexTaskView",
    "ProcessViewTemplateNames",
    "SuccessMessageMixin",
    "TaskSuccessUrlMixin",
    "TaskViewTemplateNames",
    "UpdateArtifactView",
    "UpdateProcessView",
    "UserIndexTaskView",
    "WorkflowArchiveListView",
    "WorkflowInboxListView",
    "WorkflowQueueListView",
)
