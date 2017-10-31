from __future__ import unicode_literals

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.views import generic
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _

from ...decorators import flow_start_view
from .mixins import MessageUserMixin
from .utils import get_next_task_url


class BaseStartFlowMixin(object):
    """Mixin for start views."""

    def get_context_data(self, **kwargs):
        """Context for a start view.

        :keyword activation: the task activation instance
        """
        kwargs['activation'] = self.activation
        return super(BaseStartFlowMixin, self).get_context_data(**kwargs)

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
                '{}/{}/start.html'.format(opts.app_label, opts.flow_label),
                'viewflow/flow/start.html')
        else:
            return [self.template_name]

    @method_decorator(flow_start_view)
    def dispatch(self, request, **kwargs):
        """Check user permissions, and prepare flow for execution."""
        self.activation = request.activation
        if not self.activation.has_perm(request.user):
            raise PermissionDenied

        self.activation.prepare(request.POST or None, user=request.user)
        return super(BaseStartFlowMixin, self).dispatch(request, **kwargs)


class StartFlowMixin(MessageUserMixin, BaseStartFlowMixin):
    """Mixin for flow views completes activation on a form submit."""

    def activation_done(self, *args, **kwargs):
        """Finish task activation."""
        self.activation.done()
        self.success(_('Process {process} has been started.'))

    def form_valid(self, *args, **kwargs):
        """If the form is valid, save the associated model and finish the task."""
        super(StartFlowMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())


class CreateProcessView(StartFlowMixin, generic.UpdateView): # noqa D101
    def __init__(self, *args, **kwargs):  # noqa D102
        super(CreateProcessView, self).__init__(*args, **kwargs)
        if self.form_class is None and self.fields is None:
            self.fields = []

    @property
    def model(self):
        """Process class."""
        return self.activation.flow_class.process_class

    def get_object(self):
        """Return the process for the task activation."""
        return self.activation.process
