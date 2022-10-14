from django.urls import path

from viewflow import viewprop, this
from viewflow.workflow import nodes
from . import views, mixins, utils


class Start(mixins.NodeDetailMixin, nodes.Start):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView

    @property
    def start_view(self):
        return this.resolve(self.flow_class.instance, self._start_view)

    @property
    def start_view_path(self):
        return path(f'{self.name}/', utils.wrap_start_view(self, self.start_view), name='execute')


class StartHandle(mixins.NodeDetailMixin, nodes.StartHandle):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class End(mixins.NodeDetailMixin, nodes.End):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class View(mixins.NodeDetailMixin, nodes.View):
    index_view_class = views.UserIndexTaskView
    detail_view_class = views.DetailTaskView

    """
    Execute View
    """
    @property
    def view(self):
        return this.resolve(self.flow_class.instance, self._view)

    @property
    def view_path(self):
        return path(
            f'<int:process_pk>/{self.name}/<int:task_pk>/execute/',
            utils.wrap_view(self, self.view),
            name='execute'
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
                f'<int:process_pk>/{self.name}/<int:task_pk>/assign/',
                utils.wrap_task_view(self, self.assign_view, permission=self.can_assign),
                name='assign'
            )

    """
    Unassign
    """
    unassign_view_class = None

    @viewprop
    def unassign_view(self):
        """View for a task assign."""
        if self.unassign_view_class:
            return self.unassign_view_class.as_view()

    @property
    def unassign_path(self):
        if self.assign_view:
            return path(
                f'<int:process_pk>/{self.name}/<int:task_pk>/unassign/',
                utils.wrap_task_view(self, self.unassign_view, permission=self.can_unassign),
                name='unassign'
            )


class If(mixins.NodeDetailMixin, nodes.If):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class Function(mixins.NodeDetailMixin, nodes.Function):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class Handle(mixins.NodeDetailMixin, nodes.Handle):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class Obsolete(mixins.NodeDetailMixin, nodes.Obsolete):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class Join(mixins.NodeDetailMixin, mixins.NodeExecuteMixin, nodes.Join):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class Split(mixins.NodeDetailMixin, mixins.NodeExecuteMixin, nodes.Split):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class StartSubprocess(mixins.NodeDetailMixin, nodes.StartSubprocess):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class Subprocess(mixins.NodeDetailMixin, nodes.Subprocess):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class NSubprocess(mixins.NodeDetailMixin, nodes.NSubprocess):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class Switch(mixins.NodeDetailMixin, nodes.Switch):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
