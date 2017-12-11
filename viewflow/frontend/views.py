from __future__ import unicode_literals

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import six
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.views import generic
from django.views.generic.base import TemplateResponseMixin

from material.frontend import frontend_url
from material.frontend.views.list import DataTableMixin


from ..flow.views.mixins import FlowListMixin, FlowViewPermissionMixin
from ..models import Task


class BaseTasksActionView(FlowListMixin, generic.TemplateView):
    """Base for action view for multiple tasks."""

    action_name = None
    success_url = 'viewflow:index'
    template_name = 'viewflow/site_task_action.html'

    def get_context_data(self, **kwargs):
        """Context for the action view.

        :keyword tasks: List of task.
        """
        context = super(BaseTasksActionView, self).get_context_data(**kwargs)
        context['tasks'] = self.tasks
        return context

    def get_success_url(self):
        """Continue to the flow index or redirect according `?back` parameter."""
        if 'back' in self.request.GET:
            back_url = self.request.GET['back']
            if not is_safe_url(url=back_url, host=self.request.get_host()):
                back_url = '/'
            return back_url

        return reverse(self.success_url)

    def get_tasks(self, user, task_pks):
        """List of tasks for the action.

        Subclasses should override it.
        """
        raise NotImplementedError

    def report(self, message, level=messages.INFO, fail_silently=True, **kwargs):
        """Send a notification with link to the tasks.

        :param message: A message template.
        :param level: A level, one of https://docs.djangoproject.com/en/1.10/ref/contrib/messages/#message-levels
        :param fail_silently: Raise a error if messaging framework is not installed.
        :param kwargs: Additional parametes used in format message templates.

        A `message_template` prepared by python `.format()`
        function. In addition to `kwargs`, the `{tasks}` parameter passed.

        Example::

            self.report('{process} has been cancelled.')

        """
        tasks_links = []
        for task in self.tasks:
            task_url = self.get_task_url(task, url_type='detail')
            task_link = '<a href="{task_url}">#{task_pk}</a>'.format(task_url=task_url, task_pk=task.pk)
            tasks_links.append(task_link)

        kwargs.update({
            'tasks': ' '.join(tasks_links)
        })

        message = mark_safe(_(message).format(**kwargs))

        messages.add_message(self.request, level, message, fail_silently=fail_silently)

    def success(self, message, fail_silently=True, **kwargs):
        """Notification about successful operation."""
        self.report(message, level=messages.SUCCESS, fail_silently=fail_silently, **kwargs)

    def error(self, message, fail_silently=True, **kwargs):
        """Notification about an error."""
        self.report(message, level=messages.ERROR, fail_silently=fail_silently, **kwargs)

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """Process request.GET['tasks'] parameter and perform the action."""
        requested_pks = [pk for pk in request.GET.get('tasks', '').split(',') if pk.isdigit()]
        self.tasks = self.get_tasks(request.user, requested_pks)

        return super(BaseTasksActionView, self).dispatch(request, *args, **kwargs)


class TasksUnAssignView(BaseTasksActionView):
    """Deassign multiple tasks."""

    action_name = 'unassign'

    def get_tasks(self, user, tasks_pks):
        """List of tasks assigned to the user."""
        return Task.objects.inbox(self.flows, user).filter(pk__in=tasks_pks)

    def post(self, request, *args, **kwargs):
        """Deassign tasks from the user."""
        for task in self.tasks:
            lock = task.process.flow_class.lock_impl(task.process.flow_class.instance)
            with lock(task.process.flow_class, task.process_id):
                activation = task.activate()
                activation.unassign()
        self.success('Tasks {tasks} has been unassigned.')
        return HttpResponseRedirect(self.get_success_url())


class TasksAssignView(BaseTasksActionView):
    """Assign multiple tasks."""

    action_name = 'assign'
    success_url = 'viewflow:queue'

    def get_tasks(self, user, tasks_pks):
        """List of tasks that can be assigned for the user."""
        return Task.objects.queue(self.flows, user).filter(pk__in=tasks_pks)

    def post(self, request, *args, **kwargs):
        """Assign tasks to the current user."""
        for task in self.tasks:
            lock = task.process.flow_class.lock_impl(task.process.flow_class.instance)
            with lock(task.process.flow_class, task.process_id):
                activation = task.activate()
                activation.assign(self.request.user)

        self.success('Tasks {tasks} has been assigned.')
        return HttpResponseRedirect(self.get_success_url())


@method_decorator(login_required, name='dispatch')
class AllTaskListView(FlowListMixin,
                      TemplateResponseMixin,
                      DataTableMixin,
                      generic.View):
    list_display = [
        'task_hash', 'description', 'process_summary', 'process_url', 'created'
    ]
    template_name = 'viewflow/site_tasks.html'

    def task_hash(self, task):
        task_url = frontend_url(self.request, self.get_task_url(task), back_link='here')
        return mark_safe('<a href="{}">{}/{}</a>'.format(task_url, task.process.id, task.pk))
    task_hash.short_description = _("#")

    def description(self, task):
        summary = task.summary()
        if not summary:
            summary = task.flow_task
        task_url = frontend_url(self.request, self.get_task_url(task), back_link='here')
        return mark_safe('<a href="{}">{}</a>'.format(task_url, summary))
    description.short_description = _('Task Description')

    def process_summary(self, task):
        return task.flow_process.summary()
    process_summary.short_description = _('Process Summary')

    def process_url(self, task):
        process_url = frontend_url(self.request, self.get_process_url(task.process), back_link='here')
        return mark_safe('<a href="{}">{} #{}</a>'.format(
            process_url, task.process.flow_class.process_title, task.process.pk))
    process_url.short_description = _('Process URL')

    def get_queryset(self):
        """Filtered task list."""
        queryset = Task.objects.inbox(self.flows, self.request.user)
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, six.string_types):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)
        return queryset


@method_decorator(login_required, name='dispatch')
class AllQueueListView(
        FlowListMixin,
        TemplateResponseMixin,
        DataTableMixin,
        generic.View):
    list_display = [
        'task_hash', 'description', 'process_summary',
        'process_url', 'created'
    ]
    template_name = 'viewflow/site_queue.html'

    def task_hash(self, task):
        task_url = frontend_url(self.request, self.get_task_url(task), back_link='here')
        return mark_safe('<a href="{}">{}/{}</a>'.format(task_url, task.process.id, task.pk))
    task_hash.short_description = _("#")

    def description(self, task):
        summary = task.summary()
        if not summary:
            summary = task.flow_task
        task_url = frontend_url(self.request, self.get_task_url(task), back_link='here')
        return mark_safe('<a href="{}">{}</a>'.format(task_url, summary))
    description.short_description = _('Task Description')

    def process_summary(self, task):
        return task.flow_process.summary()
    process_summary.short_description = _('Process Summary')

    def process_url(self, task):
        process_url = frontend_url(self.request, self.get_process_url(task.process), back_link='here')
        return mark_safe('<a href="{}">{} #{}</a>'.format(
            process_url, task.process.flow_class.process_title, task.process.pk))
    process_url.short_description = _('Process URL')

    def get_queryset(self):
        """Filtered task list."""
        queryset = Task.objects.queue(self.flows, self.request.user)
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, six.string_types):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)
        return queryset


@method_decorator(login_required, name='dispatch')
class AllArchiveListView(FlowListMixin,
                         TemplateResponseMixin,
                         DataTableMixin,
                         generic.View):
    list_display = [
        'task_hash', 'description', 'started',
        'finished', 'process_title', 'process_summary',
    ]
    template_name = 'viewflow/site_archive.html'

    def task_hash(self, task):
        task_url = frontend_url(self.request, self.get_task_url(task), back_link='here')
        return mark_safe('<a href="{}">{}/{}</a>'.format(task_url, task.process.id, task.pk))
    task_hash.short_description = _("#")

    def description(self, task):
        summary = task.summary()
        if not summary:
            summary = task.flow_task
        task_url = frontend_url(self.request, self.get_task_url(task), back_link='here')
        return mark_safe('<a href="{}">{}</a>'.format(task_url, summary))
    description.short_description = _('Task Description')

    def process_title(self, task):
        process_url = frontend_url(self.request, self.get_process_url(task.process), back_link='here')
        return mark_safe('<a href="{}">{} #{}</a>'.format(
            process_url, task.flow_task.flow_class.process_title, task.process.pk))
    process_title.short_description = _('Process')

    def process_summary(self, task):
        process_url = frontend_url(self.request, self.get_process_url(task.process), back_link='here')
        return mark_safe('<a href="{}">{}</a>'.format(
            process_url, task.flow_process.summary()))
    process_summary.short_description = _('Process Summary')

    def get_queryset(self):
        """All tasks from all processes assigned to the current user."""
        queryset = Task.objects.archive(self.flows, self.request.user)
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, six.string_types):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)
        return queryset


@method_decorator(login_required, name='dispatch')
class ProcessListView(FlowViewPermissionMixin,
                      TemplateResponseMixin,
                      DataTableMixin,
                      generic.View):
    list_display = [
        'process_id', 'process_summary',
        'created', 'finished', 'active_tasks'
    ]

    def get_process_link(self, process):
        url_name = '{}:detail'.format(self.request.resolver_match.namespace)
        return reverse(url_name, args=[process.pk])

    def process_id(self, process):
        return mark_safe('<a href="{}">{}</a>'.format(
            self.get_process_link(process),
            process.pk)
        )
    process_id.short_description = '#'

    def process_summary(self, process):
        return mark_safe('<a href="{}">{}</a>'.format(
            self.get_process_link(process),
            process.summary())
        )
    process_summary.short_description = 'Summary'

    def active_tasks(self, process):
        if process.finished is None:
            return mark_safe('<a href="{}">{}</a>'.format(
                self.get_process_link(process),
                process.active_tasks().count())
            )
        return ''
    active_tasks.short_description = _('Active Tasks')

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

    def get_queryset(self):
        """Filtered process list."""
        process_class = self.flow_class.process_class
        queryset = process_class.objects.filter(flow_class=self.flow_class)
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, six.string_types):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)
        return queryset
