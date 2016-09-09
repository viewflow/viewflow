from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.http import is_safe_url
from django.utils.decorators import method_decorator
from django.utils.timezone import now
from django.views import generic
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from ...activation import STATUS
from ...decorators import flow_view
from ...exceptions import FlowRuntimeError
from .mixins import (
    FlowManagePermissionMixin, FlowTaskManagePermissionMixin,
    MessageUserMixin
)


class BaseTaskActionView(MessageUserMixin, generic.TemplateView):
    action_name = None

    def can_proceed(self):
        raise NotImplementedError

    def perform(self):
        raise NotImplementedError

    def get_template_names(self):
        flow_task = self.activation.flow_task
        opts = self.activation.flow_task.flow_class._meta

        return (
            '{}/{}/{}_{}.html'.format(opts.app_label, opts.flow_label, flow_task.name, self.action_name),
            '{}/{}/task_{}.html'.format(opts.app_label, opts.flow_label, self.action_name),
            'viewflow/flow/task_{}.html'.format(self.action_name),
            'viewflow/flow/task_action.html')

    def get_success_url(self):
        return self.activation.flow_task.get_task_url(
            self.activation.task, 'detail', user=self.request.user,
            namespace=self.request.resolver_match.namespace)

    def get_context_data(self, **kwargs):
        context = super(BaseTaskActionView, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        context['flow_class'] = self.flow_class
        return context

    def post(self, request, *args, **kwargs):
        if 'run_action' in request.POST:
            self.perform()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(request, *args, **kwargs)

    @method_decorator(flow_view)
    def dispatch(self, request, **kwargs):
        self.activation = request.activation
        self.flow_class = self.activation.flow_class

        if not self.can_proceed():
            self.error("Task {task} Can't execute action {action}.", action=self.action_name.title)

            return redirect(self.activation.flow_task.get_task_url(
                self.activation.task, url_type='detail', user=request.user))

        return super(BaseTaskActionView, self).dispatch(request, **kwargs)


class UndoTaskView(FlowTaskManagePermissionMixin, BaseTaskActionView):
    action_name = 'undo'

    def can_proceed(self):
        return self.activation.undo.can_proceed()

    def perform(self):
        self.activation.undo()
        self.success('Task {task} has been undone.')


class CancelTaskView(FlowTaskManagePermissionMixin, BaseTaskActionView):
    action_name = 'cancel'

    def can_proceed(self):
        return self.activation.cancel.can_proceed()

    def perform(self):
        self.activation.cancel()
        self.success('Task {task} has been canceled.')


class PerformTaskView(FlowTaskManagePermissionMixin, BaseTaskActionView):
    """Non-interactive task that cancelled and need to be started manually."""

    action_name = 'execute'

    def can_proceed(self):
        return self.activation.perform.can_proceed()

    def perform(self):
        self.activation.perform()
        self.error('Task {task} has been executed.')


class ActivateNextTaskView(FlowTaskManagePermissionMixin, BaseTaskActionView):
    """Activate next task without interactive task redone."""

    action_name = 'activate_next'

    def can_proceed(self):
        return self.activation.activate_next.can_proceed()

    def perform(self):
        self.activation.activate_next()


class CancelProcessView(FlowManagePermissionMixin, generic.DetailView):
    context_object_name = 'process'
    pk_url_kwarg = 'process_pk'

    def report(self, message, level=messages.INFO, fail_silently=True, **kwargs):
        namespace = self.request.resolver_match.namespace

        process_url = reverse('{}:detail'.format(namespace), args=[self.object.pk])
        process_link = '<a href="{process_url}">#{process_pk}</a>'.format(
            process_url=process_url,
            process_pk=self.object.pk)
        kwargs.update({
            'process': process_link,
        })
        message = mark_safe(_(message).format(**kwargs))

        messages.add_message(self.request, level, message, fail_silently=fail_silently)

    def success(self, message, fail_silently=True, **kwargs):
        self.report(message, level=messages.SUCCESS, fail_silently=fail_silently, **kwargs)

    def error(self, message, fail_silently=True, **kwargs):
        self.report(message, level=messages.ERROR, fail_silently=fail_silently, **kwargs)

    def get_template_names(self):
        opts = self.flow_class._meta

        return (
            '{}/{}/process_cancel.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/process_cancel.html')

    def get_queryset(self):
        return self.flow_class.process_class._default_manager.all()

    def get_success_url(self):
        if 'back' in self.request.GET:
            back_url = self.request.GET['back']
            if not is_safe_url(url=back_url, host=self.request.get_host()):
                back_url = '/'
            return back_url

        return reverse('{}:index'.format(self.request.resolver_match.namespace))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.status in [STATUS.DONE, STATUS.CANCELED]:
            self.error('Process {process} can not be canceled.')
            return HttpResponseRedirect(self.get_success_url())
        elif '_cancel_process' in request.POST:
            self._cancel_active_tasks()
            self._cancel_process()
            self.success('Process {process} has been canceled.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.flow_class = kwargs['flow_class']

        lock = self.flow_class.lock_impl(self.flow_class.instance)
        with lock(self.flow_class, kwargs['process_pk']):
            return super(CancelProcessView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
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
