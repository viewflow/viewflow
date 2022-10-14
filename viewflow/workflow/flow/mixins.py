from django.urls import path
from viewflow import viewprop
from viewflow.urls import ViewsetMeta
from . import utils


class NodeDetailMixin(metaclass=ViewsetMeta):
    """Task detail view."""

    index_view_class = None

    @viewprop
    def index_view(self):
        """View for a task detail."""
        if self.index_view_class:
            return self.index_view_class.as_view()

    @property
    def index_path(self):
        if self.index_view:
            return path(
                f"<int:process_pk>/{self.name}/<int:task_pk>/",
                utils.wrap_task_view(self, self.index_view),
                name="index",
            )

    detail_view_class = None

    @viewprop
    def detail_view(self):
        """View for a task detail."""
        if self.detail_view_class:
            return self.detail_view_class.as_view()

    @property
    def detail_path(self):
        if self.detail_view:
            return path(
                f"<int:process_pk>/{self.name}/<int:task_pk>/detail/",
                utils.wrap_task_view(self, self.detail_view, permission=self.can_view),
                name="detail",
            )

    def can_view(self, user, task):
        """Check if user has a view task detail permission."""
        return self.flow_class.instance.has_view_permission(user, task)


class NodeExecuteMixin(metaclass=ViewsetMeta):
    """Re-execute a gate manually."""

    execute_view_class = None

    @viewprop
    def execute_view(self):
        """View for the admin to re-execute a gate."""
        if self.execute_view_class:
            return self.execute_view_class.as_view()

    @property
    def execute_path(self):
        if self.execute_view:
            return path(
                "<int:process_pk>/{}/<int:task_pk>/execute/".format(self.name),
                utils.wrap_task_view(self, self.execute_view),
                name="execute",
            )
