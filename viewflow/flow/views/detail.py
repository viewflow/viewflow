from django.views import generic
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from .mixins import FlowViewPermissionMixin

from ...decorators import flow_view
from .utils import flow_start_actions


class DetailTaskView(generic.TemplateView):
    """
    Default detail view for flow task.

    Get confirmation from user, assigns task and redirects to task pages.
    """

    def get_template_names(self):
        flow_task = self.activation.flow_task
        opts = self.activation.flow_task.flow_cls._meta

        return (
            '{}/{}/{}_details.html'.format(opts.app_label, opts.flow_label, flow_task.name),
            '{}/{}/task_details.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/task_details.html')

    def get_context_data(self, **kwargs):
        context = super(DetailTaskView, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        return context

    @method_decorator(flow_view)
    def dispatch(self, request, *args, **kwargs):
        self.activation = request.activation

        if not self.activation.flow_task.can_view(request.user, self.activation.task):
            raise PermissionDenied
        return super(DetailTaskView, self).dispatch(request, *args, **kwargs)


class DetailProcessView(FlowViewPermissionMixin, generic.DetailView):

    """Details for process."""

    context_object_name = 'process'
    pk_url_kwarg = 'process_pk'

    def get_template_names(self):
        opts = self.flow_cls._meta

        return (
            '{}/{}/process_details.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/process_details.html')

    def get_context_data(self, **kwargs):
        context = super(DetailProcessView, self).get_context_data(**kwargs)
        context['start_actions'] = flow_start_actions(
            self.flow_cls, namespace=self.request.resolver_match.namespace, user=self.request.user)
        context['flow_cls'] = self.flow_cls
        context['task_list'] = context['process'].task_set.all().order_by('created')
        return context

    def get_queryset(self):
        return self.flow_cls.process_cls._default_manager.all()
