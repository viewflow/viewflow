from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views import generic

from viewflow.views import ListModelView
from viewflow.utils import viewprop, has_object_perm
from viewflow.workflow import chart
from viewflow.workflow.fields import get_task_ref
from . import mixins, filters


@method_decorator(login_required, name="dispatch")
class DashboardView(
    mixins.StoreRequestPathMixin,
    mixins.ProcessViewTemplateNames,
    generic.TemplateView,
):
    """Kanban-like process dashboard view."""

    viewset = None
    flow_class = None
    template_filename = "process_dashboard.html"
    MAX_ROWS = 26

    # TODO queryset from viewset
    # @viewprop
    # def queryset(self):
    #    if self.viewset is not None and hasattr(self.viewset, 'get_task_queryset'):
    #        return self.viewset.get_queryset(self.request)
    #    return self.flow_class.task_class._default_manager

    def get_context_data(self, **kwargs):
        sorted_nodes, _ = chart.topsort(self.flow_class)
        nodes = [
            node
            for node in sorted_nodes
            if node.task_type in ["HUMAN", "JOB", "SUBPROCESS"]
        ]

        start_nodes = [
            {"node": node, "can_execute": node.can_execute(self.request.user)}
            for node in self.flow_class.instance.get_start_nodes()
        ]

        end_nodes = [node for node in sorted_nodes if node.task_type in ["END"]]

        columns = []
        for node in nodes:
            columns.append(
                {
                    "node": node,
                    "node_ref": get_task_ref(node),
                    "tasks": self.flow_class.task_class._default_manager.filter_available(
                        [self.flow_class], self.request.user
                    ).filter(
                        finished__isnull=True, flow_task=node
                    )[
                        : self.MAX_ROWS
                    ],
                }
            )

        finished = self.flow_class.task_class._default_manager.filter_available(
            [self.flow_class], self.request.user
        ).filter(finished__isnull=False, flow_task__in=end_nodes)[: self.MAX_ROWS]

        return super().get_context_data(
            columns=columns,
            start_nodes=start_nodes,
            end_nodes=end_nodes,
            finished=finished,
            **kwargs,
        )

    def has_view_permission(self, user, obj=None):
        if self.viewset is not None:
            return self.viewset.has_view_permission(user, obj=obj)
        else:
            return has_object_perm(
                user, "view", self.model, obj=obj
            ) or has_object_perm(user, "change", self.model, obj=obj)

    def dispatch(self, request, *args, **kwargs):
        if not self.has_view_permission(self.request.user):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


class DashboardTaskListView(
    mixins.StoreRequestPathMixin,
    mixins.ProcessViewTemplateNames,
    ListModelView,
):
    """List of all tasks of the flow."""

    flow_class = None
    template_filename = "task_list.html"

    columns = ("task_id", "flow_task", "process_summary", "created", "owner")
    filterset_class = filters.DashboardTaskListViewFilter

    def task_id(self, task):
        task_url = task.flow_task.reverse("index", args=[task.process_id, task.pk])
        return mark_safe(f'<a href="{task_url}">#{task.process_id}/{task.pk}</a>')

    task_id.short_description = _("#")

    def process_summary(self, task):
        return task.process.coerced.brief

    @property
    def model(self):
        return self.flow_class.task_class

    @viewprop
    def queryset(self):
        queryset = self.model._default_manager.all()
        return queryset.filter(process__flow_class=self.flow_class)


class DashboardProcessListView(
    mixins.StoreRequestPathMixin,
    mixins.ProcessViewTemplateNames,
    ListModelView,
):
    """List of all processes of the flow."""

    flow_class = None
    template_filename = "process_list.html"

    columns = ("process_id", "brief", "created", "finished", "active_tasks")
    object_link_columns = ("pk", "brief")
    filterset_class = filters.DashboardProcessListViewFilter

    def process_id(self, process):
        process_url = self.request.resolver_match.flow_viewset.reverse(
            "process_detail", args=[process.pk]
        )
        return mark_safe(f'<a href="{process_url}">{process.pk}</a>')

    def active_tasks(self, obj):
        manager = obj.flow_class.task_class._default_manager
        return manager.filter(process=obj, finished__isnull=True).count()

    @property
    def model(self):
        return self.flow_class.process_class

    def get_queryset(self):
        """Filtered process list."""
        queryset = super().get_queryset()
        return queryset.filter(flow_class=self.flow_class)
