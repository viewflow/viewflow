from django.urls import path

from viewflow import viewprop, this
from viewflow.workflow import nodes
from . import views, mixins, utils


class Start(mixins.NodeDetailMixin, mixins.NodeUndoMixin, nodes.Start):
    """
    The Start node in a flow.
    """

    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView

    @property
    def start_view(self):
        return this.resolve(self.flow_class.instance, self._start_view)

    @property
    def start_view_path(self):
        return path(
            f"{self.name}/",
            utils.wrap_start_view(self, self.start_view),
            name="execute",
        )


class StartHandle(mixins.NodeDetailMixin, mixins.NodeUndoMixin, nodes.StartHandle):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView


class End(
    mixins.NodeDetailMixin, mixins.NodeUndoMixin, mixins.NodeReviveMixin, nodes.End
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView


class View(
    mixins.NodeDetailMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    mixins.NodeReviveMixin,
    nodes.View,
):
    index_view_class = views.UserIndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView

    """
    Execute View
    """

    @property
    def view(self):
        return this.resolve(self.flow_class.instance, self._view)

    @property
    def view_path(self):
        return path(
            f"<int:process_pk>/{self.name}/<int:task_pk>/execute/",
            utils.wrap_view(self, self.view),
            name="execute",
        )

    """
    Assign user to a task
    """
    assign_view_class = views.AssignTaskView

    @viewprop
    def assign_view(self):
        """View for a task assign."""
        if self.assign_view_class:
            return self.assign_view_class.as_view()

    @property
    def assign_path(self):
        if self.assign_view:
            return path(
                f"<int:process_pk>/{self.name}/<int:task_pk>/assign/",
                utils.wrap_task_view(
                    self, self.assign_view, permission=self.can_assign
                ),
                name="assign",
            )

    """
    Unassign
    """
    unassign_view_class = views.UnassignTaskView

    @viewprop
    def unassign_view(self):
        """View for a task assign."""
        if self.unassign_view_class:
            return self.unassign_view_class.as_view()

    @property
    def unassign_path(self):
        if self.unassign_view:
            return path(
                f"<int:process_pk>/{self.name}/<int:task_pk>/unassign/",
                utils.wrap_task_view(
                    self, self.unassign_view, permission=self.can_unassign
                ),
                name="unassign",
            )


class If(
    mixins.NodeDetailMixin, mixins.NodeUndoMixin, mixins.NodeReviveMixin, nodes.If
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView


class Function(mixins.NodeDetailMixin, mixins.NodeUndoMixin, nodes.Function):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView


class Handle(
    mixins.NodeDetailMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    mixins.NodeReviveMixin,
    nodes.Handle,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView


class Obsolete(mixins.NodeDetailMixin, mixins.NodeCancelMixin, nodes.Obsolete):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView


class Join(
    mixins.NodeDetailMixin,
    mixins.NodeExecuteMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    mixins.NodeReviveMixin,
    nodes.Join,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView


class Split(
    mixins.NodeDetailMixin,
    mixins.NodeExecuteMixin,
    mixins.NodeUndoMixin,
    mixins.NodeReviveMixin,
    nodes.Split,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView


class SplitFirst(
    mixins.NodeDetailMixin,
    nodes.SplitFirst,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class StartSubprocess(
    mixins.NodeDetailMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    nodes.StartSubprocess,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView


class Subprocess(
    mixins.NodeDetailMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    nodes.Subprocess,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView


class NSubprocess(
    mixins.NodeDetailMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    nodes.NSubprocess,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView


class Switch(
    mixins.NodeDetailMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    mixins.NodeReviveMixin,
    nodes.Switch,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView
