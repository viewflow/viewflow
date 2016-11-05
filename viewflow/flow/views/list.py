from django.views import generic
from django.utils.translation import ugettext_lazy as _
from django_filters import FilterSet, ChoiceFilter, DateRangeFilter, ModelChoiceFilter

from ... import activation, models
from ...fields import import_task_by_ref
from .mixins import (
    LoginRequiredMixin, FlowViewPermissionMixin,
    FlowListMixin
)


class TaskFilter(FilterSet):
    """Filter for a task list."""

    flow_task = ChoiceFilter(help_text='')
    created = DateRangeFilter(help_text='')
    process = ModelChoiceFilter(queryset=models.Process.objects.all(), help_text='')

    def __init__(self, data=None, queryset=None, prefix=None, strict=None):  # noqa D102
        super(TaskFilter, self).__init__(data=data, queryset=queryset, prefix=prefix, strict=strict)
        self.filters['process'].field.queryset = \
            models.Process.objects.filter(id__in=queryset.values_list('process', flat=True))

        def task_name(task_ref):
            flow_task = import_task_by_ref(task_ref)
            return "{}/{}".format(flow_task.flow_class.process_title, flow_task.name.title())

        tasks = [(task_ref, task_name(task_ref))
                 for task_ref in queryset.order_by('flow_task').distinct().values_list('flow_task', flat=True)]

        self.filters['flow_task'].field.choices = [(None, 'All')] + tasks

    class Meta:  # noqa D101
        fields = ['process', 'flow_task', 'created']
        model = models.Task


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

    def __init__(self, *args, **kwargs):  # noqa D102
        self._filter = None
        super(AllTaskListView, self).__init__(*args, **kwargs)

    def get_queryset(self):
        """Filtered task list."""
        return self.filter.qs

    @property
    def filter(self):
        """Apply a task filter."""
        if self._filter is None:
            self._filter = TaskFilter(self.request.GET, self.get_base_queryset(self.request.user))
        return self._filter

    def get_base_queryset(self, user):
        """All tasks from all processes assigned to the current user."""
        return models.Task.objects.inbox(self.flows, user).order_by('-created')


class AllQueueListView(LoginRequiredMixin, FlowListMixin, generic.ListView):
    """All unassigned tasks available for the current user."""

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'queue'
    template_name = 'viewflow/site_queue.html'

    def __init__(self, *args, **kwargs):  # noqa D102
        self._filter = None
        super(AllQueueListView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        """Context for a view."""
        context = super(AllQueueListView, self).get_context_data(**kwargs)
        context['filter'] = self.filter
        return context

    def get_queryset(self):
        """Filtered task list."""
        return self.filter.qs

    @property
    def filter(self):
        """Apply a task filter."""
        if self._filter is None:
            self._filter = TaskFilter(self.request.GET, self.get_base_queryset(self.request.user))
        return self._filter

    def get_base_queryset(self, user):
        """All unassigned tasks available for the current user."""
        return models.Task.objects.queue(self.flows, user).order_by('-created')


class AllArchiveListView(LoginRequiredMixin, FlowListMixin, generic.ListView):
    """All tasks from all processes assigned to the current user."""

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'task_list'
    template_name = 'viewflow/site_archive.html'

    def get_queryset(self):
        """All tasks from all processes assigned to the current user."""
        return models.Task.objects.archive(self.flows, self.request.user).order_by('-created')


class ProcessFilter(FilterSet):
    """Process list filter."""

    status = ChoiceFilter(help_text='', choices=(
        (None, _('All')),
        (activation.STATUS.NEW, _('Active')),
        (activation.STATUS.CANCELED, _('Canceled')),
        (activation.STATUS.DONE, _('Completed')),
    ))
    created = DateRangeFilter(help_text='')
    finished = DateRangeFilter(help_text='')


class ProcessListView(FlowViewPermissionMixin, generic.ListView):
    """List of processes available for the current user."""

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'process_list'

    def __init__(self, *args, **kwargs):  # noqa D102
        self._filter = None
        super(ProcessListView, self).__init__(*args, **kwargs)

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
        return self.filter.qs

    @property
    def filter(self):
        """Apply a process filter."""
        if self._filter is None:
            self._filter = ProcessFilter(self.request.GET, self.get_base_queryset(self.request.user))
        return self._filter

    def get_base_queryset(self, user):
        """List of processes available for the current user."""
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

    def get_context_data(self, **kwargs):
        """Context for a task list view."""
        context = super(TaskListView, self).get_context_data(**kwargs)
        context['flow_class'] = self.flow_class
        return context

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

    def get_context_data(self, **kwargs):
        """Context for a queue view."""
        context = super(QueueListView, self).get_context_data(**kwargs)
        context['flow_class'] = self.flow_class
        return context

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

    def get_context_data(self, **kwargs):
        """Context for a detail view."""
        context = super(QueueListView, self).get_context_data(**kwargs)
        context['flow_class'] = self.flow_class
        return context

    def get_queryset(self):
        """List of task completed by the current user."""
        manager = self.flow_class.task_class._default_manager

        return manager.user_archive(
            self.request.user,
            flow_class=self.flow_class
        ).order_by('-created')
