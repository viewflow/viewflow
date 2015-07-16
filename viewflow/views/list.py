from collections import OrderedDict

from django.views import generic
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django_filters import FilterSet, ChoiceFilter, DateRangeFilter

from .. import activation, flow, models
from ..fields import import_task_by_ref
from .base import FlowViewPermissionMixin


def flow_start_actions(flow_cls, user=None):
    """
    Return list of start flow actions data available
    """
    actions = []
    for node in flow_cls._meta.nodes():
        if isinstance(node, flow.Start) and (user is None or node.can_execute(user)):
            node_url = reverse('{}:{}'.format(flow_cls.instance.namespace, node.name))
            actions.append((node_url, node.name))

    return actions


def flows_start_actions(flow_classes, user=None):
    actions = OrderedDict()

    for flow_cls in sorted(flow_classes, key=lambda flow_cls: flow_cls.process_title):
        actions[flow_cls] = flow_start_actions(flow_cls, user)
    return actions


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)


class TaskFilter(FilterSet):
    flow_task = ChoiceFilter()
    created = DateRangeFilter()

    def __init__(self, data=None, queryset=None, prefix=None, strict=None):
        super(TaskFilter, self).__init__(data=data, queryset=queryset, prefix=prefix, strict=strict)
        self.filters['process'].field.queryset = \
            models.Process.objects.filter(id__in=queryset.values_list('process', flat=True))

        def task_name(task_ref):
            flow_task = import_task_by_ref(task_ref)
            return "{}/{}".format(flow_task.flow_cls.process_title, flow_task.name.title())

        tasks = [(task_ref, task_name(task_ref))
                 for task_ref in queryset.order_by('flow_task').distinct().values_list('flow_task', flat=True)]

        self.filters['flow_task'].field.choices = [(None, 'All')] + tasks

    class Meta:
        fields = ['process', 'flow_task', 'created']
        model = models.Task


class AllListViewTemplateResponseMixin(object):
    app_label = None

    def get_template_names(self):
        if self.app_label is None:
            return 'viewflow/{}'.format(self.template_name)
        else:
            return (
                '{}/{}'.format(self.app_label, self.template_name),
                'viewflow/{}'.format(self.template_name))


class ListViewTemplateResponseMixin(object):
    def get_template_names(self):
        opts = self.flow_cls._meta

        return (
            '{}/{}/{}'.format(opts.app_label, opts.flow_label, self.template_name),
            '{}/flow/{}'.format(opts.app_label, self.template_name),
            'viewflow/flow/{}'.format(self.template_name))


class AllProcessListView(AllListViewTemplateResponseMixin, LoginRequiredMixin, generic.ListView):
    """
    All process instances list available for current user
    """
    flow_classes = []

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'process_list'

    template_name = 'site_index.html'

    def get_context_data(self, **kwargs):
        context = super(AllProcessListView, self).get_context_data(**kwargs)
        context['start_actions'] = flows_start_actions(self.flow_classes, self.request.user)
        return context

    def get_queryset(self):
        return models.Process.objects \
            .filter_available(self.flow_classes, self.request.user) \
            .order_by('-created')


class AllTaskListView(AllListViewTemplateResponseMixin, generic.ListView):
    """
    All tasks from all processes assigned to current user
    """
    flow_classes = []

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'task_list'

    template_name = 'site_tasks.html'

    def get_context_data(self, **kwargs):
        context = super(AllTaskListView, self).get_context_data(**kwargs)
        context['start_actions'] = flows_start_actions(self.flow_classes, self.request.user)
        context['filter'] = self.filter
        return context

    def get_queryset(self):
        return self.filter.qs

    def get_base_queryset(self, user):
        return models.Task.objects.inbox(self.flow_classes, user).order_by('-created')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.filter = TaskFilter(request.GET, self.get_base_queryset(request.user))
        return super(AllTaskListView, self).dispatch(request, *args, **kwargs)


class AllQueueListView(AllListViewTemplateResponseMixin, generic.ListView):
    """
    All unassigned tasks available for current user
    """
    flow_classes = []

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'queue'

    template_name = 'site_queue.html'

    def get_context_data(self, **kwargs):
        context = super(AllQueueListView, self).get_context_data(**kwargs)
        context['start_actions'] = flows_start_actions(self.flow_classes, self.request.user)
        context['filter'] = self.filter
        return context

    def get_queryset(self):
        return self.filter.qs

    def get_base_queryset(self, user):
        return models.Task.objects.queue(self.flow_classes, user).order_by('-created')

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        self.filter = TaskFilter(request.GET, self.get_base_queryset(request.user))
        return super(AllQueueListView, self).dispatch(request, *args, **kwargs)


class AllArchiveListView(AllListViewTemplateResponseMixin, LoginRequiredMixin, generic.ListView):
    """
    All tasks from all processes assigned to current user
    """
    flow_classes = []

    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'task_list'

    template_name = 'site_archive.html'

    def get_context_data(self, **kwargs):
        context = super(AllArchiveListView, self).get_context_data(**kwargs)
        context['start_actions'] = flows_start_actions(self.flow_classes, self.request.user)
        return context

    def get_queryset(self):
        return models.Task.objects.archive(self.flow_classes, self.request.user).order_by('-created')


class ProcessListView(ListViewTemplateResponseMixin, FlowViewPermissionMixin, generic.ListView):
    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'process_list'

    template_name = 'process_list.html'

    def get_context_data(self, **kwargs):
        context = super(ProcessListView, self).get_context_data(**kwargs)
        context['start_actions'] = flow_start_actions(self.flow_cls, self.request.user)
        context['flow_cls'] = self.flow_cls
        return context

    def get_queryset(self):
        return self.flow_cls.process_cls.objects \
            .filter(flow_cls=self.flow_cls) \
            .order_by('-created')


class ProcessDetailView(ListViewTemplateResponseMixin, FlowViewPermissionMixin, generic.DetailView):
    """
    Details for process
    """
    context_object_name = 'process'
    pk_url_kwarg = 'process_pk'

    template_name = 'process_details.html'

    def get_context_data(self, **kwargs):
        context = super(ProcessDetailView, self).get_context_data(**kwargs)
        context['start_actions'] = flow_start_actions(self.flow_cls, self.request.user)
        context['flow_cls'] = self.flow_cls
        context['task_list'] = context['process'].task_set.all().order_by('created')
        return context

    def get_queryset(self):
        return self.flow_cls.process_cls._default_manager.all()


class TaskListView(ListViewTemplateResponseMixin, FlowViewPermissionMixin, generic.ListView):
    """
    List of specific Flow tasks assigned to current user
    """
    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'task_list'

    template_name = 'task_list.html'

    def get_context_data(self, **kwargs):
        context = super(TaskListView, self).get_context_data(**kwargs)
        context['start_actions'] = flow_start_actions(self.flow_cls, self.request.user)
        context['flow_cls'] = self.flow_cls
        return context

    def get_queryset(self):
        return self.flow_cls.task_cls.objects \
            .filter(process__flow_cls=self.flow_cls,
                    owner=self.request.user,
                    status=activation.STATUS.ASSIGNED) \
            .order_by('-created')


class QueueListView(ListViewTemplateResponseMixin, FlowViewPermissionMixin, generic.ListView):
    """
    List of specific Flow unassigned tasks available for current user
    """
    paginate_by = 15
    paginate_orphans = 5
    context_object_name = 'queue'

    template_name = 'queue.html'

    def get_context_data(self, **kwargs):
        context = super(QueueListView, self).get_context_data(**kwargs)
        context['start_actions'] = flow_start_actions(self.flow_cls, self.request.user)
        context['flow_cls'] = self.flow_cls
        return context

    def get_queryset(self):
        queryset = self.flow_cls.task_cls.objects.user_queue(self.request.user, flow_cls=self.flow_cls) \
            .filter(status=activation.STATUS.NEW).order_by('-created')

        return queryset
