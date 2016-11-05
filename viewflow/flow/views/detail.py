from django.views import generic
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied

from ...decorators import flow_view
from .mixins import FlowViewPermissionMixin


class DetailTaskView(generic.TemplateView):
    """
    Default detail view for the flow task.

    Get confirmation from user, assigns task and redirects to task pages.
    """

    def get_template_names(self):
        """List of template names to be used for a process detail page.

        If `template_name` is None, default value is::

            [<app_label>/<flow_label>/<task_name>_detail.html,
             <app_label>/<flow_label>/task_detail.html,
             'viewflow/flow/task_detail.html']
        """
        if self.template_name is None:
            flow_task = self.activation.flow_task
            opts = self.activation.flow_task.flow_class._meta

            return (
                '{}/{}/{}_detail.html'.format(opts.app_label, opts.flow_label, flow_task.name),
                '{}/{}/task_detail.html'.format(opts.app_label, opts.flow_label),
                'viewflow/flow/task_detail.html')
        else:
            return [self.template_name]

    def get_context_data(self, **kwargs):
        """Context for a detail view.

        :keyword activation: the task activation instance
        """
        context = super(DetailTaskView, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        return context

    @method_decorator(flow_view)
    def dispatch(self, request, *args, **kwargs):
        """Check permissions and show task detail."""
        self.activation = request.activation

        if not self.activation.flow_task.can_view(request.user, self.activation.task):
            raise PermissionDenied
        return super(DetailTaskView, self).dispatch(request, *args, **kwargs)


class DetailProcessView(FlowViewPermissionMixin, generic.DetailView):
    """Detail for process."""

    context_object_name = 'process'
    pk_url_kwarg = 'process_pk'

    def get_template_names(self):
        """List of template names to be used for a process detail page.

        If `template_name` is None, default value is::

            [<app_label>/<flow_label>/process_detail.html,
             'viewflow/flow/process_detail.html']
        """
        if self.template_name is None:
            opts = self.flow_class._meta

            return (
                '{}/{}/process_detail.html'.format(opts.app_label, opts.flow_label),
                'viewflow/flow/process_detail.html')
        else:
            return [self.template_name]

    def get_context_data(self, **kwargs):
        """Context for a detail view.

        :keyword process: a Process instance
        :keyword task_list: List of tasks of the process
        """
        context = super(DetailProcessView, self).get_context_data(**kwargs)
        context['task_list'] = context['process'].task_set.all().order_by('created')
        return context

    def get_queryset(self):
        """Return the `QuerySet` that will be used to look up the process."""
        if self.queryset is None:
            return self.flow_class.process_class._default_manager.all()
        return self.queryset.all()
