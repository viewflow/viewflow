from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.timezone import now
from django.utils.http import is_safe_url
from django.utils.safestring import mark_safe
from django.views import generic
from django.utils.translation import ugettext_lazy as _

from ..activation import STATUS
from ..exceptions import FlowRuntimeError
from .base import FlowManagePermissionMixin, BaseTaskActionView, \
    get_task_hyperlink, get_process_hyperlink


class ProcessCancelView(FlowManagePermissionMixin, generic.DetailView):
    flow_cls = None
    context_object_name = 'process'
    pk_url_kwarg = 'process_pk'

    def get_template_names(self):
        opts = self.flow_cls._meta

        return (
            '{}/{}/process_cancel.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/process_cancel.html')

    def get_queryset(self):
        return self.flow_cls.process_cls._default_manager.all()

    def get_success_url(self):
        if 'back' in self.request.GET:
            back_url = self.request.GET['back']
            if not is_safe_url(url=back_url, host=self.request.get_host()):
                back_url = '/'
            return back_url

        return reverse('{}:index'.format(self.object.flow_cls.instance.namespace))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.status in [STATUS.DONE, STATUS.CANCELED]:
            hyperlink = get_process_hyperlink(self.object)
            msg = _('Process {hyperlink} can not be canceled.').format(hyperlink=hyperlink)
            messages.error(self.request, mark_safe(msg), fail_silently=True)
            return HttpResponseRedirect(self.get_success_url())
        elif '_cancel_process' in request.POST:
            self._cancel_active_tasks()
            self._cancel_process()
            hyperlink = get_process_hyperlink(self.object)
            msg = _('Process {hyperlink} has been canceled.').format(hyperlink=hyperlink)
            messages.info(self.request, mark_safe(msg), fail_silently=True)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.flow_cls = kwargs.pop('flow_cls', None)

        lock = self.flow_cls.lock_impl(self.flow_cls.instance)
        with lock(self.flow_cls, kwargs['process_pk']):
            return super(ProcessCancelView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProcessCancelView, self).get_context_data(**kwargs)
        context['active_tasks'] = self._get_task_list()
        context['flow_cls'] = self.flow_cls
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


class TaskUndoView(FlowManagePermissionMixin, BaseTaskActionView):
    action_name = 'undo'

    def can_proceed(self):
        return self.activation.undo.can_proceed()

    def perform(self):
        self.activation.undo()
        hyperlink = get_task_hyperlink(self.activation.task, self.request.user)
        msg = _('Task {hyperlink} has been undone.').format(hyperlink=hyperlink)
        messages.info(self.request, mark_safe(msg), fail_silently=True)


class TaskCancelView(FlowManagePermissionMixin, BaseTaskActionView):
    action_name = 'cancel'

    def can_proceed(self):
        return self.activation.cancel.can_proceed()

    def perform(self):
        self.activation.cancel()
        hyperlink = get_task_hyperlink(self.activation.task, self.request.user)
        msg = _('Task {hyperlink} has been canceled.').format(hyperlink=hyperlink)
        messages.info(self.request, mark_safe(msg), fail_silently=True)


class TaskPerformView(FlowManagePermissionMixin, BaseTaskActionView):
    """Non-interactive task that cancelled and need to be started manually."""

    action_name = 'execute'

    def can_proceed(self):
        return self.activation.perform.can_proceed()

    def perform(self):
        self.activation.perform()
        hyperlink = get_task_hyperlink(self.activation.task, self.request.user)
        msg = _('Task {hyperlink} has been executed.').format(hyperlink=hyperlink)
        messages.success(self.request, mark_safe(msg), fail_silently=True)


class TaskActivateNextView(FlowManagePermissionMixin, BaseTaskActionView):
    """Activate next task without interactive task redone."""

    action_name = 'activate_next'

    def can_proceed(self):
        return self.activation.activate_next.can_proceed()

    def perform(self):
        self.activation.activate_next()


class TaskUnAssignView(BaseTaskActionView):
    action_name = 'unassign'

    def can_proceed(self):
        if self.activation.unassign.can_proceed():
            return self.activation.flow_task.can_unassign(self.request.user, self.activation.task)
        return False

    def perform(self):
        self.activation.unassign()
        hyperlink = get_task_hyperlink(self.activation.task, self.request.user)
        msg = _('Task {hyperlink} has been unassigned.').format(hyperlink=hyperlink)
        messages.info(self.request, mark_safe(msg), fail_silently=True)
