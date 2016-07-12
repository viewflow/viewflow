from django.core.exceptions import PermissionDenied
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
        opts = self.activation.flow_task.flow_cls._meta

        return (
            '{}/{}/{}.html'.format(opts.app_label, opts.flow_label, flow_task.name),
            '{}/{}/start.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/start.html')

    def activation_done(self, *args, **kwargs):
        """Finish activation."""
        self.activation.done()

    @method_decorator(flow_start_view)
    def dispatch(self, request, **kwargs):
        """Check user permissions, and prepare flow to execution."""
        self.activation = request.activation
        if not self.activation.has_perm(request.user):
            raise PermissionDenied

        self.activation.prepare(request.POST or None, user=request.user)
        return super(BaseStartFlowMixin, self).dispatch(request, **kwargs)


class StartFlowMixin(MessageUserMixin, BaseStartFlowMixin):
    def form_valid(self, *args, **kwargs):
        response = super(StartFlowMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self.success('Process {process} has been started.')
        return response


class StartFlowView(StartFlowMixin, generic.UpdateView):
    fields = []

    @property
    def model(self):
        return self.activation.flow_cls.process_cls

    def get_object(self):
        return self.activation.process
