from django.views import generic
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.decorators import method_decorator

from .. import flow, models


def _available_flows(flow_classes, user):
    result = []
    for flow_cls in flow_classes:
        opts = flow_cls.process_cls._meta
        view_perm = "{}.view_{}".format(opts.app_label, opts.model_name)
        if user.has_perm(view_perm):
            result.append(flow_cls)
    return result


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class FlowPermissionMixin(object):
    flow_cls = None

    def dispatch(self, *args, **kwargs):
        self.flow_cls = kwargs.get('flow_cls', self.flow_cls)
        opts = self.flow_cls.process_cls._meta
        view_perm = "{}.view_{}".format(opts.app_label, opts.model_name)

        return permission_required(view_perm)(super(FlowPermissionMixin, self).dispatch)(*args, **kwargs)


class AllProcessListView(LoginRequiredMixin, generic.ListView):
    """
    All process instances list available for current user
    """
    flow_classes = []

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'process_list'

    def get_template_names(self):
        return 'viewflow/site_index.html'

    def get_queryset(self):
        return models.Process.objects \
            .coerce_for(_available_flows(self.flow_classes, self.request.user)) \
            .order_by('-created')


class AllTaskListView(LoginRequiredMixin, generic.ListView):
    """
    All tasks from all processes assigned to current user
    """
    flow_classes = []

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'task_list'

    def get_template_names(self):
        return 'viewflow/site_tasks.html'

    def get_queryset(self):
        return models.Task.objects \
            .coerce_for(_available_flows(self.flow_classes, self.request.user)) \
            .filter(owner=self.request.user, status=models.Task.STATUS.ASSIGNED) \
            .order_by('-created')


class AllQueueListView(LoginRequiredMixin, generic.ListView):
    """
    All unassigned tasks available for current user
    """
    flow_classes = []

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'queue'

    def get_template_names(self):
        return 'viewflow/site_queue.html'

    def get_queryset(self):
        queryset = models.Task.objects \
            .coerce_for(_available_flows(self.flow_classes, self.request.user)) \
            .user_queue(self.request.user) \
            .filter(status=models.Task.STATUS.NEW) \
            .order_by('-created')

        return queryset


class ProcessListView(FlowPermissionMixin, generic.ListView):
    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'process_list'

    def get_template_names(self):
        opts = self.flow_cls._meta

        return (
            '{}/{}/process_list.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/process_list.html')

    def available_start_actions(self):
        """
        Return list of start flow actions data available for the user
        """

        actions = []
        for node in self.flow_cls._meta.nodes():
            if isinstance(node, flow.Start) and node.can_execute(self.request.user):
                node_url = reverse(
                    '{}:{}'.format(self.flow_cls.instance.namespace, node.name))

                actions.append((node_url, node.name))

        return actions

    def get_context_data(self, **kwargs):
        context = super(ProcessListView, self).get_context_data(**kwargs)
        context['start_actions'] = self.available_start_actions()
        context['flow_cls'] = self.flow_cls
        return context

    def get_queryset(self):
        return self.flow_cls.process_cls.objects \
            .filter(flow_cls=self.flow_cls) \
            .order_by('-created')


class ProcessDetailView(FlowPermissionMixin, generic.DetailView):
    """
    Details for process
    """
    context_object_name = 'process'
    pk_url_kwarg = 'process_pk'

    def get_template_names(self):
        opts = self.flow_cls._meta

        return (
            '{}/{}/process_details.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/process_details.html')

    def get_context_data(self, **kwargs):
        context = super(ProcessDetailView, self).get_context_data(**kwargs)
        context['flow_cls'] = self.flow_cls
        context['task_list'] = context['process'].task_set.all().order_by('created')
        return context

    def get_queryset(self):
        return self.flow_cls.process_cls._default_manager.all()


class TaskListView(FlowPermissionMixin, generic.ListView):
    """
    List of specific Flow tasks assigned to current user
    """
    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'task_list'

    def get_template_names(self):
        opts = self.flow_cls._meta

        return (
            '{}/{}/task_list.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/task_list.html')

    def get_context_data(self, **kwargs):
        context = super(TaskListView, self).get_context_data(**kwargs)
        context['flow_cls'] = self.flow_cls
        return context

    def get_queryset(self):
        return self.flow_cls.task_cls.objects \
            .filter(process__flow_cls=self.flow_cls,
                    owner=self.request.user,
                    status=self.flow_cls.task_cls.STATUS.ASSIGNED) \
            .order_by('-created')


class QueueListView(FlowPermissionMixin, generic.ListView):
    """
    List of specific Flow unassigned tasks available for current user
    """
    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'queue'

    def get_template_names(self):
        opts = self.flow_cls._meta

        return (
            '{}/{}/queue.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/queue.html')

    def get_context_data(self, **kwargs):
        context = super(QueueListView, self).get_context_data(**kwargs)
        context['flow_cls'] = self.flow_cls
        return context

    def get_queryset(self):
        queryset = self.flow_cls.task_cls.objects.user_queue(self.request.user, flow_cls=self.flow_cls) \
            .filter(status=self.flow_cls.task_cls.STATUS.NEW).order_by('-created')

        return queryset
