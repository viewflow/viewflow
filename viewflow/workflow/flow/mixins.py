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


class NodeUndoMixin(metaclass=ViewsetMeta):
    """Allow to undo a completed task."""

    undo_view_class = None

    @viewprop
    def undo_view(self):
        """View for the admin to undo a task."""
        if self.undo_view_class:
            return self.undo_view_class.as_view()

    @property
    def undo_path(self):
        if self.undo_view:
            return path(
                f"<int:process_pk>/{self.name}/<int:task_pk>/undo/",
                utils.wrap_task_view(self, self.undo_view, permission=self.can_undo),
                name="undo",
            )

    def can_undo(self, user, task):
        return self.flow_class.instance.has_manage_permission(user)


class NodeCancelMixin(metaclass=ViewsetMeta):
    """Cancel a task action."""

    cancel_view_class = None

    @viewprop
    def cancel_view(self):
        """View for the admin to cancel a task."""
        if self.cancel_view_class:
            return self.cancel_view_class.as_view()

    @property
    def cancel_path(self):
        if self.cancel_view:
            return path(
                f"<int:process_pk>/{self.name}/<int:task_pk>/cancel/",
                utils.wrap_task_view(self, self.cancel_view, permission=self.can_cancel),
                name="cancel",
            )

    def can_cancel(self, user, task):
        return self.flow_class.instance.has_manage_permission(user)


class NodeReviveMixin(metaclass=ViewsetMeta):
    """Review a canceled task"""

    revive_view_class = None

    @viewprop
    def revive_view(self):
        """View for the admin to cancel a task."""
        if self.revive_view_class:
            return self.revive_view_class.as_view()

    @property
    def revive_path(self):
        if self.revive_view:
            return path(
                f"<int:process_pk>/{self.name}/<int:task_pk>/revive/",
                utils.wrap_task_view(self, self.revive_view, permission=self.can_revive),
                name="revive",
            )

    def can_revive(self, user, task):
        return self.flow_class.instance.has_manage_permission(user)


