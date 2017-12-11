from __future__ import unicode_literals

from django.utils.six.moves.urllib.parse import quote as urlquote

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views import generic
from django.utils.decorators import method_decorator
from django.utils.http import is_safe_url
from django.utils.translation import ugettext_lazy as _

from ...decorators import flow_view
from .actions import BaseTaskActionView
from .mixins import MessageUserMixin
from .utils import get_next_task_url


class BaseFlowMixin(object):
    """Mixin for a task views."""

    def get_context_data(self, **kwargs):
        """Context for a task view.

        :keyword activation: the task activation instance
        """
        context = super(BaseFlowMixin, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        return context

    def get_success_url(self):
        """Continue on task or redirect back to task list."""
        return get_next_task_url(self.request, self.activation.process)

    def get_template_names(self):
        """List of template names to be used for a task view.

        If `template_name` is None, default value is::

            [<app_label>/<flow_label>/<task_name>.html,
             <app_label>/<flow_label>/task.html,
             'viewflow/flow/task.html']
        """
        if self.template_name is None:
            flow_task = self.activation.flow_task
            opts = self.activation.flow_task.flow_class._meta

            return (
                '{}/{}/{}.html'.format(opts.app_label, opts.flow_label, flow_task.name),
                '{}/{}/task.html'.format(opts.app_label, opts.flow_label),
                'viewflow/flow/task.html')
        else:
            return [self.template_name]

    @method_decorator(flow_view)
    def dispatch(self, request, **kwargs):
        """Lock the process, initialize `self.activation`, check permission and execute."""
        self.activation = request.activation

        if not self.activation.prepare.can_proceed():
            self.error(_('Task {task} cannot be executed.'))
            return redirect(self.activation.flow_task.get_task_url(
                self.activation.task, url_type='detail', user=request.user,
                namespace=self.request.resolver_match.namespace))

        if not self.activation.has_perm(request.user):
            raise PermissionDenied

        self.activation.prepare(request.POST or None)
        return super(BaseFlowMixin, self).dispatch(request, **kwargs)


class FlowMixin(MessageUserMixin, BaseFlowMixin):
    """Mixin for flow views completes activation on a form submit."""

    def activation_done(self, *args, **kwargs):
        """Finish the task activation."""
        self.activation.done()
        self.success(_('Task {task} has been completed.'))
        if self.activation.process.finished:
            self.success(_('Process {process} has been completed.'))

    def form_valid(self, *args, **kwargs):
        """If the form is valid, save the associated model and finish the task."""
        super(FlowMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())


FlowViewMixin = FlowMixin  # TODO Remove


class UpdateProcessView(FlowMixin, generic.UpdateView):  # noqa D101
    def __init__(self, *args, **kwargs):  # noqa D102
        super(UpdateProcessView, self).__init__(*args, **kwargs)
        if self.form_class is None and self.fields is None:
            self.fields = []

    @property
    def model(self):
        """Process class."""
        return self.activation.flow_class.process_class

    def get_object(self, queryset=None):
        """Return the process for the task activation."""
        return self.activation.process


class AssignTaskView(MessageUserMixin, generic.TemplateView):
    """
    Default assign view for flow task.

    Get confirmation from user, assigns task and redirects to task pages
    """

    action_name = 'assign'

    def get_template_names(self):
        """List of template names to be used for a process detail page.

        If `template_name` is None, default value is::

            [<app_label>/<flow_label>/<task_name>_assign.html,
             <app_label>/<flow_label>/task_assign.html,
             'viewflow/flow/task_assign.html']
        """
        if self.template_name is None:
            flow_task = self.activation.flow_task
            opts = self.activation.flow_class._meta

            return (
                '{}/{}/{}_assign.html'.format(opts.app_label, opts.flow_label, flow_task.name),
                '{}/{}/task_assign.html'.format(opts.app_label, opts.flow_label),
                'viewflow/flow/task_assign.html')
        else:
            return [self.template_name]

    def get_context_data(self, **kwargs):
        """Context for a detail view.

        :keyword activation: the task activation instance
        """
        context = super(AssignTaskView, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        return context

    def get_success_url(self):
        """Continue on task or redirect back to task list."""
        url = self.activation.flow_task.get_task_url(
            self.activation.task, url_type='guess', user=self.request.user,
            namespace=self.request.resolver_match.namespace)

        back = self.request.GET.get('back', None)
        if back and not is_safe_url(url=back, host=self.request.get_host()):
            back = '/'

        if '_continue' in self.request.POST and back:
            url = "{}?back={}".format(url, urlquote(back))
        elif back:
            url = back

        return url

    def post(self, request, *args, **kwargs):
        """
        Assign task to the current user.

        Expect that form submitted with `_continue` or `_assign` button::

            <button type="submit" name="_continue">Assign and continue on this process</button>
            <button type="submit" name="_assign">Assign</button>
        """
        if '_assign' or '_continue' in request.POST:
            self.activation.assign(self.request.user)
            self.success(_('Task {task} has been assigned'))
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(request, *args, **kwargs)

    @method_decorator(flow_view)
    def dispatch(self, request, *args, **kwargs):
        """Check permissions and assign task to the current user."""
        self.activation = request.activation

        if request.user is None or request.user.is_anonymous:
            raise PermissionDenied

        if not self.activation.assign.can_proceed():
            self.error(_('Task {task} cannot be assigned to you'))
            return redirect(self.activation.flow_task.get_task_url(
                self.activation.task, url_type='detail', user=request.user,
                namespace=self.request.resolver_match.namespace))

        if not self.activation.flow_task.can_assign(request.user, self.activation.task):
            raise PermissionDenied

        return super(AssignTaskView, self).dispatch(request, *args, **kwargs)


class UnassignTaskView(BaseTaskActionView):
    """Deassign task from the current owner."""

    action_name = 'unassign'

    def can_proceed(self):
        """Check that task is assigned and user has rights to deassign it."""
        if self.activation.unassign.can_proceed():
            return self.activation.flow_task.can_unassign(self.request.user, self.activation.task)
        return False

    def perform(self):
        """Unassign the task from the current owner."""
        self.activation.unassign()
        self.success(_('Task {task} has been unassigned.'))
