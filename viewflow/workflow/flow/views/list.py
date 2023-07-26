from django.urls import reverse_lazy
from django.utils.safestring import mark_safe
from django.utils.timesince import timesince
from django.utils.translation import gettext_lazy as _

from viewflow.views import ListModelView, Action
from viewflow.utils import viewprop
from viewflow.workflow.status import STATUS
from viewflow.workflow.models import Task
from . import filters, mixins


class FlowInboxListView(
    mixins.StoreRequestPathMixin,
    mixins.ProcessViewTemplateNames,
    ListModelView,
):
    """List of current user assigned tasks of a flow"""

    flow_class = None
    template_filename = "process_tasks_list.html"
    title = _('Inbox')

    columns = ("task_id", "flow_task", "brief", "created")
    filterset_class = filters.FlowUserTaskListFilter

    def task_id(self, task):
        task_url = task.flow_task.reverse("index", args=[task.process_id, task.pk])
        return mark_safe(f'<a href="{task_url}">#{task.process_id}/{task.pk}</a>')

    task_id.short_description = _("#")

    @property
    def model(self):
        return self.flow_class.task_class

    @viewprop
    def queryset(self):
        """List of tasks assigned to the current user."""
        queryset = self.model._default_manager.all()

        return queryset.filter(
            process__flow_class=self.flow_class,
            owner=self.request.user,
            status=STATUS.ASSIGNED,
        ).order_by("-created")


class FlowQueueListView(
    mixins.StoreRequestPathMixin,
    mixins.ProcessViewTemplateNames,
    ListModelView,
):
    """List of current user available tasks of a flow"""

    columns = ("task_id", "flow_task", "brief", "created")
    filterset_class = filters.FlowUserTaskListFilter
    flow_class = None
    template_filename = "process_tasks_list.html"
    title = _('Queue')

    def task_id(self, task):
        task_url = task.flow_task.reverse("index", args=[task.process_id, task.pk])
        return mark_safe(f'<a href="{task_url}">#{task.process_id}/{task.pk}</a>')

    task_id.short_description = _("#")

    @property
    def model(self):
        return self.flow_class.task_class

    @viewprop
    def queryset(self):
        """List of tasks available to the current user."""
        queryset = self.model._default_manager.all()

        return (
            queryset.user_queue(self.request.user, flow_class=self.flow_class)
            .filter(status=STATUS.NEW)
            .order_by("-created")
        )


class FlowArchiveListView(
    mixins.StoreRequestPathMixin,
    mixins.ProcessViewTemplateNames,
    ListModelView,
):
    """List of current user completed tasks of a flow."""

    columns = ("task_id", "brief", "created", "finished", "process_summary")
    filterset_class = filters.FlowArchiveListFilter
    flow_class = None
    template_filename = "process_tasks_list.html"
    title = _('Archive')

    def task_id(self, task):
        task_url = task.flow_task.reverse("index", args=[task.process_id, task.pk])
        return mark_safe(f'<a href="{task_url}">#{task.process_id}/{task.pk}</a>')

    task_id.short_description = _("#")

    def process_summary(self, task):
        process_url = self.request.resolver_match.flow_viewset.reverse(
            "process_detail", args=[task.process_id]
        )
        return mark_safe(f'<a href="{process_url}">{task.process.brief}</a>')

    @property
    def model(self):
        return self.flow_class.task_class

    @viewprop
    def queryset(self):
        """List of task completed by the current user."""
        queryset = self.model._default_manager.all().select_related("process")

        return queryset.user_archive(
            self.request.user, flow_class=self.flow_class
        ).order_by("-created")


class WorkflowTaskListView(mixins.StoreRequestPathMixin, ListModelView):
    flow_classes = None
    model = Task
    template_name = "viewflow/workflow/workflow_tasks_list.html"

    def task_id(self, task):
        task_url = task.flow_task.reverse("index", args=[task.process_id, task.pk])
        return mark_safe(f'<a href="{task_url}">#{task.process_id}/{task.pk}</a>')

    task_id.short_description = _("#")

    def flow_task(self, task):
        return _(str(task.flow_task))

    flow_task.short_description = _("Task")

    def process_brief(self, task):
        flow_viewset = task.flow_task.flow_class.parent
        process_url = flow_viewset.reverse("process_detail", args=[task.process_id])
        return mark_safe(f'<a href="{process_url}">{task.process.brief}</a>')

    def flows_start_nodes(self):
        return {
            flow_class: start_nodes
            for flow_class in self.flow_classes
            if (start_nodes := flow_class.get_start_nodes(self.request.user))
        }


class WorkflowInboxListView(WorkflowTaskListView):
    """List of current user assigned tasks from all viewset registered flows."""

    columns = ("task_id", "flow_task", "brief", "process_brief", "created")
    bulk_actions = (
        Action(name=_("Unassign selected tasks"), viewname="tasks_unassign"),
    )
    title = _('Inbox')

    filterset_class = filters.FlowUserTaskListFilter

    @viewprop
    def queryset(self):
        """List of tasks assigned to the current user."""
        return self.model._default_manager.inbox(self.flow_classes, self.request.user)

    def created(self, task):
        return timesince(task.created)


class WorkflowQueueListView(WorkflowTaskListView):
    """List of current user available tasks from all viewset registered flows."""

    columns = ("task_id", "process_brief", "flow_task", "brief", "created")
    filterset_class = filters.FlowUserTaskListFilter
    bulk_actions = (Action(name=_("Assign selected tasks"), viewname="tasks_assign"),)
    title = _('Queue')

    @viewprop
    def queryset(self):
        return self.model._default_manager.queue(self.flow_classes, self.request.user)


class WorkflowArchiveListView(WorkflowTaskListView):
    """List of current user participated tasks from all viewset registered flows."""

    columns = ("task_id", "flow_task", "brief", "process_brief", "created", "finished")
    filterset_class = filters.FlowArchiveListFilter
    title = _('Archive')

    @viewprop
    def queryset(self):
        return self.model._default_manager.archive(self.flow_classes, self.request.user)
