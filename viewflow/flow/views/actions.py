from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from ...activation import STATUS
from ...decorators import flow_view
from ...exceptions import FlowRuntimeError
from .mixins import (
    FlowManagePermissionMixin, FlowTaskManagePermissionMixin,
    MessageUserMixin
)


class BaseTaskActionView(MessageUserMixin, generic.TemplateView):
    """Base class for the basic flow action views."""

    action_name = None
    action_title = None

    def can_proceed(self):
        """Check that action can be executed.

        Subclasses should override it.
        """
        raise NotImplementedError

    def perform(self):
        """
        Perform the action.

        Subclasses should override it.
        """
        raise NotImplementedError

    def get_template_names(self):
        """List of template names to be used for a action view.

        If `template_name` is None, default value is::

            [<app_label>/<flow_label>/<task_name>_<action_name>.html,
             <app_label>/<flow_label>/task_<action_name>.html,
             'viewflow/flow/task_<action_name>.html'
             'viewflow/flow/task_action.html']
        """
        if self.template_name is None:
            flow_task = self.activation.flow_task
            opts = self.activation.flow_task.flow_class._meta

            return (
                '{}/{}/{}_{}.html'.format(opts.app_label, opts.flow_label, flow_task.name, self.action_name),
                '{}/{}/task_{}.html'.format(opts.app_label, opts.flow_label, self.action_name),
                'viewflow/flow/task_{}.html'.format(self.action_name),
                'viewflow/flow/task_action.html')
        else:
            return [self.template_name]

    def get_success_url(self):
        """Continue on task or redirect back to task list."""
        return self.activation.flow_task.get_task_url(
            self.activation.task, 'detail', user=self.request.user,
            namespace=self.request.resolver_match.namespace)

    def get_context_data(self, **kwargs):
        """Context for a task view.

        :keyword activation: the task activation instance
        """
        context = super(BaseTaskActionView, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        context['flow_class'] = self.flow_class
        return context

    def post(self, request, *args, **kwargs):
        """Perform the action.

        Expect that form submitted with `run_action` button::

            <button type="submit" name="run_action">Perform</button>

        """
        if 'run_action' in request.POST:
            self.perform()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(request, *args, **kwargs)

    @method_decorator(flow_view)
    def dispatch(self, request, **kwargs):
        """Activate the task and check the permission."""
        self.activation = request.activation
        self.flow_class = self.activation.flow_class

        if not self.can_proceed():
            self.error("Task {task} Can't execute action {action}.", action=self.action_name.title)

            return redirect(self.activation.flow_task.get_task_url(
                self.activation.task, url_type='detail', user=request.user,
                namespace=self.request.resolver_match.namespace))

        return super(BaseTaskActionView, self).dispatch(request, **kwargs)


class UndoTaskView(FlowTaskManagePermissionMixin, BaseTaskActionView):
    """Undo the task."""

    action_name = 'undo'
    action_title = _('Undo')

    def can_proceed(self):
        """Check that node can be undone."""
        return self.activation.undo.can_proceed()

    def perform(self):
        """Undo the node."""
        self.activation.undo()
        self.success(_('Task {task} has been undone.'))


class CancelTaskView(FlowTaskManagePermissionMixin, BaseTaskActionView):
    """Cancel task view."""

    action_name = 'cancel'
    action_title = _('Cancel')

    def can_proceed(self):
        """Check that node can be cancelled."""
        return self.activation.cancel.can_proceed()

    def perform(self):
        """Cancel the node."""
        self.activation.cancel()
        self.success(_('Task {task} has been canceled.'))


class PerformTaskView(FlowTaskManagePermissionMixin, BaseTaskActionView):
    """Non-interactive task that cancelled and need to be started manually."""

    action_name = 'execute'
    action_title = _('Perform')

    def can_proceed(self):
        """Check that gateway can be re-executed."""
        return self.activation.perform.can_proceed()

    def perform(self):
        """Rerun gateway manually."""
        self.activation.perform()
        self.error('Task {task} has been executed.')


class ActivateNextTaskView(FlowTaskManagePermissionMixin, BaseTaskActionView):
    """Activate next task without interactive task redone."""

    action_name = 'activate_next'
    action_title = _('Activate Next')

    def can_proceed(self):
        """Check that node in a state allows to activate outgoing nodes."""
        return self.activation.activate_next.can_proceed()

    def perform(self):
        """Activate outgoing nodes."""
        self.activation.activate_next()


class CancelProcessView(FlowManagePermissionMixin, generic.DetailView):
    """View to cancel a process and all active tasks."""

    context_object_name = 'process'
    pk_url_kwarg = 'process_pk'

    def report(self, message, level=messages.INFO, fail_silently=True, **kwargs):
        """Send a notification with link to the current process or task.

        :param message: A message template.
        :param level: A level, one of https://docs.djangoproject.com/en/1.10/ref/contrib/messages/#message-levels
        :param fail_silently: Raise a error if messaging framework is not installed.
        :param kwargs: Additional parametes used in format message templates.

        A `message_template` prepared by python `.format()`
        function. In addition to `kwargs`, the `{process}` parameter passed.

        Example::

            self.report('{process} has been cancelled.')

        """
        namespace = self.request.resolver_match.namespace

        process_url = reverse('{}:detail'.format(namespace), args=[self.object.pk])
        process_link = '<a href="{process_url}">#{process_pk}</a>'.format(
            process_url=process_url,
            process_pk=self.object.pk)
        kwargs.update({
            'process': process_link,
        })
        message = mark_safe(message.format(**kwargs))

        messages.add_message(self.request, level, message, fail_silently=fail_silently)

    def success(self, message, fail_silently=True, **kwargs):
        """Notification about successful operation."""
        self.report(message, level=messages.SUCCESS, fail_silently=fail_silently, **kwargs)

    def error(self, message, fail_silently=True, **kwargs):
        """Notification about an error."""
        self.report(message, level=messages.ERROR, fail_silently=fail_silently, **kwargs)

    def get_template_names(self):
        """List of template names to be used for a cancel view.

        If `template_name` is None, default value is::

            [<app_label>/<flow_label>/process_Cancel.html,
             'viewflow/flow/process_cancel.html']
        """
        if self.template_name is None:
            opts = self.flow_class._meta

            return (
                '{}/{}/process_cancel.html'.format(opts.app_label, opts.flow_label),
                'viewflow/flow/process_cancel.html')
        else:
            return [self.template_name]

    def get_queryset(self):
        """Flow processes."""
        return self.flow_class.process_class._default_manager.all()

    def get_success_url(self):
        """Continue to the flow index or redirect according `?back` parameter."""
        if 'back' in self.request.GET:
            back_url = self.request.GET['back']
            if not is_safe_url(url=back_url, host=self.request.get_host()):
                back_url = '/'
            return back_url

        return reverse('{}:index'.format(self.request.resolver_match.namespace))

    def post(self, request, *args, **kwargs):
        """Cancel active tasks and the process."""
        self.object = self.get_object()

        if self.object.status in [STATUS.DONE, STATUS.CANCELED]:
            self.error(_('Process {process} can not be canceled.'))
            return HttpResponseRedirect(self.get_success_url())
        elif '_cancel_process' in request.POST:
            self._cancel_active_tasks()
            self._cancel_process()
            self.success(_('Process {process} has been canceled.'))
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        """Lock the process."""
        self.flow_class = kwargs['flow_class']

        lock = self.flow_class.lock_impl(self.flow_class.instance)
        with lock(self.flow_class, kwargs['process_pk']):
            return super(CancelProcessView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Context for a task view.

        :keyword active_tasks: List of all tasks not finished at that moment
        :keyword uncancelable_tasks: List of tasks that can't be cancelled
        """
        context = super(CancelProcessView, self).get_context_data(**kwargs)
        context['active_tasks'] = self._get_task_list()
        context['flow_class'] = self.flow_class
        context['uncancelable_tasks'] = self._get_uncancelable_tasks(context['active_tasks'])
        return context

    def _get_task_list(self):
        active_tasks = self.object.task_set.exclude(status__in=[STATUS.DONE, STATUS.CANCELED])
        return active_tasks

    def _get_uncancelable_tasks(self, tasks):
        uncancelable = []

        for task in tasks:
            activation = task.activate()
            can_cancel = hasattr(activation, 'cancel') and activation.cancel.can_proceed()
            can_undo = hasattr(activation, 'undo') and activation.undo.can_proceed()

            if not can_undo and not can_cancel:
                uncancelable.append(task)

        return uncancelable

    def _cancel_active_tasks(self):
        active_tasks = self._get_task_list()
        for task in active_tasks:
            activation = task.activate()
            can_cancel = hasattr(activation, 'cancel') and activation.cancel.can_proceed()
            can_undo = hasattr(activation, 'undo') and activation.undo.can_proceed()

            if not can_cancel and can_undo:
                activation.undo()
                activation.cancel()
            elif can_cancel:
                activation.cancel()
            else:
                raise FlowRuntimeError("Can't cancel {}".format(task))

    def _cancel_process(self):
        self.object.status = STATUS.CANCELED
        self.object.finished = now()
        self.object.save()
