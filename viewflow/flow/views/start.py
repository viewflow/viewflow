from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.views import generic
from django.utils.decorators import method_decorator

from ...decorators import flow_start_view
from .mixins import MessageUserMixin
from .utils import get_next_task_url


class BaseStartFlowMixin(object):

    """Mixin for start views, that do not implement activation interface."""

    def get_context_data(self, **kwargs):
        """Add ``activation`` to context data."""
        kwargs['activation'] = self.activation
        return super(BaseStartFlowMixin, self).get_context_data(**kwargs)

    def get_success_url(self):
        return get_next_task_url(self.request, self.activation.process)

    def get_template_names(self):
        flow_task = self.activation.flow_task
        opts = self.activation.flow_task.flow_class._meta

        return (
            '{}/{}/{}.html'.format(opts.app_label, opts.flow_label, flow_task.name),
            '{}/{}/start.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/start.html')

    @method_decorator(flow_start_view)
    def dispatch(self, request, **kwargs):
        """Check user permissions, and prepare flow to execution."""
        self.activation = request.activation
        if not self.activation.has_perm(request.user):
            raise PermissionDenied

        self.activation.prepare(request.POST or None, user=request.user)
        return super(BaseStartFlowMixin, self).dispatch(request, **kwargs)


class StartFlowMixin(MessageUserMixin, BaseStartFlowMixin):
    def activation_done(self, *args, **kwargs):
        """Finish activation."""
        self.activation.done()
        self.success('Process {process} has been started.')

    def form_valid(self, *args, **kwargs):
        super(StartFlowMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())


class CreateProcessView(StartFlowMixin, generic.UpdateView):
    def __init__(self, *args, **kwargs):
        super(CreateProcessView, self).__init__(*args, **kwargs)
        if self.form_class is None and self.fields is None:
            self.fields = []

    @property
    def model(self):
        return self.activation.flow_class.process_class

    def get_object(self):
        return self.activation.process
