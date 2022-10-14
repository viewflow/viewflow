from django_filters import (
    DateRangeFilter,
    ChoiceFilter,
    FilterSet,
    ModelChoiceFilter as BaseModelChoiceFilter,
    MultipleChoiceFilter
)

from viewflow.this_object import this
from viewflow.workflow.status import STATUS
from viewflow.workflow.fields import get_task_ref
from viewflow.workflow.models import Process, Task


class NullDateRangeFilter(DateRangeFilter):
    def filter(self, qs, value):
        if not value:
            if not self.parent.data.get('status'):
                return qs.filter(**{f'{self.field_name}__isnull': True})
        return super().filter(qs, value)


class ModelChoiceFilter(BaseModelChoiceFilter):
    def get_queryset(self, request):
        queryset = this.resolve(self.parent, self.queryset)
        if callable(queryset):
            return queryset(request)
        return queryset


def get_queryset_flow_task_choices(queryset):
    # TODO add Node.task_name/label method
    def task_name(flow_task):
        return "{}/{}".format(flow_task.flow_class.process_title, flow_task.name.title())

    tasks = queryset.order_by('flow_task').values_list('flow_task', flat=True).distinct()
    return [
        (get_task_ref(flow_task), task_name(flow_task))
        for flow_task in tasks
    ]


class FlowUserTaskListFilter(FilterSet):
    process = ModelChoiceFilter(queryset=this.queue_processes_query)
    flow_task = ChoiceFilter()
    created = DateRangeFilter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['flow_task'].field.choices = get_queryset_flow_task_choices(self.queryset)

    def queue_processes_query(self, request):
        return Process.objects.filter(
            pk__in=self.queryset.values('process')
        )

    class Meta:
        model = Task
        fields = ('process', 'flow_task', 'created')


class FlowArchiveListFilter(FilterSet):
    flow_task = ChoiceFilter()
    created = DateRangeFilter()
    finished = DateRangeFilter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['flow_task'].field.choices = get_queryset_flow_task_choices(self.queryset)

    class Meta:
        model = Task
        fields = ('flow_task', 'created', 'finished')


class DashboardTaskListViewFilter(FilterSet):
    flow_task = ChoiceFilter()
    status = MultipleChoiceFilter(choices=STATUS.choices)
    created = DateRangeFilter()
    finished = NullDateRangeFilter()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['flow_task'].field.choices = get_queryset_flow_task_choices(self.queryset)

    class Meta:
        model = Task
        fields = ['flow_task', 'status', 'created', 'finished']


class DashboardProcessListViewFilter(FilterSet):
    created = DateRangeFilter()
    finished = NullDateRangeFilter()

    class Meta:
        model = Process
        fields = ['status', 'created', 'finished']
