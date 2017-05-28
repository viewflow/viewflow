from __future__ import unicode_literals

from django.views import generic

from ... import activation, models
from .mixins import (
    LoginRequiredMixin, FlowViewPermissionMixin,
    FlowListMixin
)


class AllProcessListView(LoginRequiredMixin, FlowListMixin, generic.ListView):
    """All process instances list available for the current user."""

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'process_list'
    template_name = 'viewflow/site_index.html'

    def get_queryset(self):
        """All process instances list available for the current user."""
        return models.Process.objects \
            .filter_available(self.flows, self.request.user) \
            .order_by('-created')


class AllTaskListView(LoginRequiredMixin, FlowListMixin, generic.ListView):
    """All tasks from all processes assigned to the current user."""

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'task_list'
    template_name = 'viewflow/site_tasks.html'

    def get_queryset(self):
        """Filtered task list."""
        return models.Task.objects.inbox(self.flows, self.request.user).order_by('-created')


class AllQueueListView(LoginRequiredMixin, FlowListMixin, generic.ListView):
    """All unassigned tasks available for the current user."""

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'queue'
    template_name = 'viewflow/site_queue.html'

    def get_queryset(self):
        """Filtered task list."""
        return models.Task.objects.queue(self.flows, self.request.user).order_by('-created')


class AllArchiveListView(LoginRequiredMixin, FlowListMixin, generic.ListView):
    """All tasks from all processes assigned to the current user."""

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'task_list'
    template_name = 'viewflow/site_archive.html'

    def get_queryset(self):
        """All tasks from all processes assigned to the current user."""
        return models.Task.objects.archive(self.flows, self.request.user).order_by('-created')


class ProcessListView(FlowViewPermissionMixin, generic.ListView):
    """List of processes available for the current user."""

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'process_list'

    def get_template_names(self):
        """List of template names to be used for an queue list view.

        If `template_name` is None, default value is::

            [<app_label>/<flow_label>/process_list.html,
             'viewflow/flow/process_list.html']
        """
        if self.template_name is None:
            opts = self.flow_class._meta

            return (
                '{}/{}/process_list.html'.format(opts.app_label, opts.flow_label),
                'viewflow/flow/process_list.html')
        else:
            return [self.template_name]

    def get_context_data(self, **kwargs):
        """Context for a view."""
        context = super(ProcessListView, self).get_context_data(**kwargs)
        context['flow_class'] = self.flow_class
        return context

    def get_queryset(self):
        """Filtered process list."""
        return self.flow_class.process_class.objects \
            .filter(flow_class=self.flow_class) \
            .order_by('-created')


class TaskListView(FlowViewPermissionMixin, generic.ListView):
    """List of tasks assigned to the current user."""

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'task_list'

    def get_template_names(self):
        """List of template names to be used for an queue list view.

        If `template_name` is None, default value is::

            [<app_label>/<flow_label>/task_list.html,
             'viewflow/flow/task_list.html']
        """
        if self.template_name is None:
            opts = self.flow_class._meta

            return (
                '{}/{}/task_list.html'.format(opts.app_label, opts.flow_label),
                'viewflow/flow/task_list.html')
        else:
            return [self.template_name]

    def get_queryset(self):
        """List of tasks assigned to the current user."""
        return self.flow_class.task_class.objects \
            .filter(process__flow_class=self.flow_class,
                    owner=self.request.user,
                    status=activation.STATUS.ASSIGNED) \
            .order_by('-created')


class QueueListView(FlowViewPermissionMixin, generic.ListView):
    """List of unassigned tasks available for current user."""

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'queue'

    def get_template_names(self):
        """List of template names to be used for an queue list view.

        If `template_name` is None, default value is::

            [<app_label>/<flow_label>/queue.html,
             'viewflow/flow/queue.html']
        """
        if self.template_name is None:
            opts = self.flow_class._meta

            return (
                '{}/{}/queue.html'.format(opts.app_label, opts.flow_label),
                'viewflow/flow/queue.html')
        else:
            return [self.template_name]

    def get_queryset(self):
        """List of unassigned tasks available for current user."""
        queryset = self.flow_class.task_class.objects.user_queue(self.request.user, flow_class=self.flow_class) \
            .filter(status=activation.STATUS.NEW).order_by('-created')

        return queryset


class ArchiveListView(FlowViewPermissionMixin, generic.ListView):
    """List of task completed by the current user."""

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'task_list'

    def get_template_names(self):
        """List of template names to be used for an archive list view.

        If `template_name` is None, default value is::

            [<app_label>/<flow_label>/archive.html,
             'viewflow/flow/archive.html']
        """
        if self.template_name is None:
            opts = self.flow_class._meta

            return (
                '{}/{}/archive.html'.format(opts.app_label, opts.flow_label),
                'viewflow/flow/archive.html')
        else:
            return [self.template_name]

    def get_queryset(self):
        """List of task completed by the current user."""
        manager = self.flow_class.task_class._default_manager

        return manager.user_archive(
            self.request.user,
            flow_class=self.flow_class
        ).order_by('-created')
