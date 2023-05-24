from django.views.generic import RedirectView
from django.urls import path
from django.utils.http import url_has_allowed_host_and_scheme as is_safe_url
from django.utils.translation import gettext_lazy as _

from viewflow import viewprop
from viewflow.utils import DEFAULT
from viewflow.urls import Application, AppMenuMixin, Viewset, ViewsetMeta
from ..status import STATUS
from ..models import Task
from . import views


class BaseFlowViewsMixin(metaclass=ViewsetMeta):
    """Common Views for Flow and FlowApp viewsets"""

    def __init__(self, flow_class, **kwargs):
        super().__init__(**kwargs)
        self._flow_class = flow_class

    def filter_kwargs(self, view_class, **kwargs):
        return super().filter_kwargs(
            view_class, **{"flow_class": self._flow_class, "viewset": self, **kwargs}
        )

    """
    Permissions
    """

    def has_view_permission(self, user, obj=None):
        return self._flow_class.instance.has_view_permission(user)

    """
    Dashboard
    """

    dashboard_view_class = views.DashboardView

    def get_dashboard_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.dashboard_view_class, **kwargs)

    @viewprop
    def dashboard_view(self):
        return self.dashboard_view_class.as_view(**self.get_dashboard_view_kwargs())

    @property
    def index_path(self):
        return path("", self.dashboard_view, name="index")

    """
    Process list
    """

    process_list_view_class = views.DashboardProcessListView

    def get_process_list_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.process_list_view_class, **kwargs)

    @viewprop
    def process_list_view(self):
        return self.process_list_view_class.as_view(
            **self.get_process_list_view_kwargs()
        )

    @property
    def process_list_path(self):
        return path("flows/", self.process_list_view, name="process_list")

    """
    Process detail
    """
    process_detail_view_class = views.DetailProcessView

    def get_process_detail_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.process_detail_view_class, **kwargs)

    @viewprop
    def process_detail_view(self):
        return self.process_detail_view_class.as_view(
            **self.get_process_detail_view_kwargs()
        )

    @property
    def process_detail_path(self):
        return path(
            "<int:process_pk>/", self.process_detail_view, name="process_detail"
        )

    """
    Process cancel
    """
    process_cancel_view_class = views.CancelProcessView

    def get_process_cancel_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.process_cancel_view_class, **kwargs)

    @viewprop
    def process_cancel_view(self):
        return self.process_cancel_view_class.as_view(
            **self.get_process_cancel_view_kwargs()
        )

    @property
    def process_cancel_path(self):
        return path(
            "<int:process_pk>/cancel/", self.process_cancel_view, name="process_cancel"
        )

    """
    Task list
    """

    task_list_view_class = views.DashboardTaskListView

    def get_task_list_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.task_list_view_class, **kwargs)

    @viewprop
    def task_list_view(self):
        return self.task_list_view_class.as_view(**self.get_task_list_view_kwargs())

    @property
    def task_list_path(self):
        return path("tasks/", self.task_list_view, name="task_list")

    """
    Chart View
    """

    chart_view_class = views.FlowChartView

    def get_chart_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.chart_view_class, **kwargs)

    @viewprop
    def chart_view(self):
        return self.chart_view_class.as_view(**self.get_chart_view_kwargs())

    @property
    def chart_path(self):
        return path("chart/", self.chart_view, name="chart")

    @property
    def flow_chart_path(self):
        return path("<int:process_pk>/chart/", self.chart_view, name="process_chart")

    """
    Utils
    """

    def get_success_url(self, request):
        if not hasattr(request, "activation"):
            return self.reverse("index")

        if "_continue" in request.POST:
            manager = self._flow_class.task_class._default_manager

            next_user_task = request.activation.task
            if next_user_task.status == STATUS.DONE:
                next_user_task = manager.next_user_task(
                    request.activation.process,
                    request.user,
                )

            if next_user_task:
                return next_user_task.flow_task.reverse(
                    "index", args=[next_user_task.process_id, next_user_task.pk]
                )

        if "back" in request.GET:
            back_url = request.GET["back"]
            if not is_safe_url(url=back_url, allowed_hosts={request.get_host()}):
                back_url = "/"
            return back_url

        if hasattr(request, "session") and "vf-pin-location" in request.session:
            back_url = request.session.get("vf-pin-location", "")
            if not is_safe_url(url=back_url, allowed_hosts={request.get_host()}):
                back_url = "/"
            return back_url

        return self.reverse("process_detail", args=[request.activation.process.pk])


class BulkActionsViewsMixin(metaclass=ViewsetMeta):
    """
    Bulk Assign Tasks
    """

    tasks_assign_view_class = views.BulkAssignTasksActionView

    def get_tasks_assign_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.tasks_assign_view_class, **kwargs)

    @viewprop
    def tasks_assign_view(self):
        return self.tasks_assign_view_class.as_view(
            **self.get_tasks_assign_view_kwargs()
        )

    @property
    def tasks_assign_path(self):
        return path("queue/assign/", self.tasks_assign_view, name="tasks_assign")

    """
    Bulk Unassign Tasks
    """
    tasks_unassign_view_class = views.BulkUnassignTasksActionView

    def get_tasks_unassign_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.tasks_unassign_view_class, **kwargs)

    @viewprop
    def tasks_unassign_view(self):
        return self.tasks_unassign_view_class.as_view(
            **self.get_tasks_unassign_view_kwargs()
        )

    @property
    def tasks_unassign_path(self):
        return path("inbox/unassign/", self.tasks_unassign_view, name="tasks_unassign")


class FlowViewset(BaseFlowViewsMixin, AppMenuMixin, Viewset):
    """Basic flow viewset."""

    def _get_urls(self):
        own_patterns = super()._get_urls()
        flow_patterns, _, _ = self._flow_class.instance.urls
        self._flow_class.parent = self
        self._flow_class.app_name = None

        return own_patterns + flow_patterns

    @viewprop
    def app_name(self):
        # assert (
        #     self._flow_class.instance.app_name
        # ), "Flow can't be connected to urlpatterns more than one time"
        return self._flow_class.instance.app_name

    @viewprop
    def title(self):
        return self._flow_class.process_title

    def _get_resolver_extra(self):
        return {"flow_viewset": self, **super()._get_resolver_extra()}


class FlowAppViewset(BaseFlowViewsMixin, BulkActionsViewsMixin, Application):
    """Viewset includes flow as an separate App into Site."""

    menu_template_name = "viewflow/workflow/flow_menu.html"
    base_template_name = "viewflow/workflow/base_page.html"

    """
    Inbox
    """

    inbox_view_class = views.FlowInboxListView

    def get_inbox_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.inbox_view_class, **kwargs)

    @viewprop
    def inbox_view(self):
        return self.inbox_view_class.as_view(**self.get_inbox_view_kwargs())

    @property
    def inbox_path(self):
        return path("inbox/", self.inbox_view, name="inbox")

    """
    Queue
    """

    queue_view_class = views.FlowQueueListView

    def get_queue_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.queue_view_class, **kwargs)

    @viewprop
    def queue_view(self):
        return self.queue_view_class.as_view(**self.get_queue_view_kwargs())

    @property
    def queue_path(self):
        return path("queue/", self.queue_view, name="queue")

    """
    Archive
    """

    archive_view_class = views.FlowArchiveListView

    def get_archive_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.archive_view_class, **kwargs)

    @viewprop
    def archive_view(self):
        return self.archive_view_class.as_view(**self.get_archive_view_kwargs())

    @property
    def archive_path(self):
        return path("archive/", self.archive_view, name="archive")

    """
    Other staff
    """

    def _get_urls(self):
        own_patterns = super()._get_urls()
        flow_patterns, _, _ = self._flow_class.instance.urls
        self._flow_class.parent = self
        self._flow_class.app_name = None

        return own_patterns + flow_patterns

    def _get_resolver_extra(self):
        return {
            "app": self,
            "viewset": self,
            "flow_viewset": self,
            "flow": self._flow_class.instance,
        }

    @viewprop
    def app_name(self):
        return self._flow_class.instance.app_name

    @viewprop
    def title(self):
        return self._flow_class.process_title

    def get_context_data(self, request):
        manager = self._flow_class.task_class._default_manager

        inbox = manager.inbox([self._flow_class], request.user)

        queue = manager.queue([self._flow_class], request.user)

        return {
            "user_inbox": inbox,
            "user_queue": queue,
        }


class _IndexRedirectView(RedirectView):
    viewset = None

    def get_redirect_url(self, *args, **kwargs):
        if self.viewset:
            redirect = None

            for flow_class in self.viewset.parent.flow_classes:
                if flow_class.instance.has_view_permission(self.request.user):
                    redirect = flow_class.instance.reverse("index")
                    break

            if redirect is None:
                raise ValueError(
                    "Can't determine index url. Please add an explicit "
                    "`index_path = path('', RedirectView(url='...'), name='index')`"
                    " declaration for the viewset"
                )
            return redirect
        return super().get_redirect_url(*args, **kwargs)


class NestedFlowsApp(AppMenuMixin, Application):
    app_name = "flows"
    title = _("Processes")
    icon = "notes"

    """
    Permissions
    """

    def has_view_permission(self, user, obj=None):
        return self.parent.has_view_permission(user, obj=obj)

    @property
    def index_path(self):
        return path("", _IndexRedirectView.as_view(viewset=self), name="index")


class WorkflowAppViewset(BulkActionsViewsMixin, Application):
    """ """

    app_name = "workflow"
    icon = "assignment"
    menu_template_name = "viewflow/workflow/workflow_menu.html"
    base_template_name = "viewflow/workflow/base_page.html"

    def __init__(self, flow_viewsets, **kwargs):
        self.flow_classes = [viewset._flow_class for viewset in flow_viewsets]

        viewsets = kwargs.get("viewsets", [])
        viewsets.append(NestedFlowsApp(viewsets=flow_viewsets))
        kwargs["viewsets"] = viewsets
        super().__init__(**kwargs)

    def _get_resolver_extra(self):
        return {
            "app": self,
            "viewset": self,
        }

    def filter_kwargs(self, view_class, **kwargs):
        return super().filter_kwargs(
            view_class, **{"flow_classes": self.flow_classes, "viewset": self, **kwargs}
        )

    """
    Permissions
    """

    def has_view_permission(self, user, obj=None):
        return any(
            flow_class.instance.has_view_permission(user, obj=obj)
            for flow_class in self.flow_classes
        )

    """
    Inbox
    """

    inbox_view_class = views.WorkflowInboxListView

    def get_inbox_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.inbox_view_class, **kwargs)

    @viewprop
    def inbox_view(self):
        return self.inbox_view_class.as_view(**self.get_inbox_view_kwargs())

    @property
    def inbox_path(self):
        return path("inbox/", self.inbox_view, name="inbox")

    """
    Queue
    """

    queue_view_class = views.WorkflowQueueListView

    def get_queue_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.queue_view_class, **kwargs)

    @viewprop
    def queue_view(self):
        return self.queue_view_class.as_view(**self.get_queue_view_kwargs())

    @property
    def queue_path(self):
        return path("queue/", self.queue_view, name="queue")

    """
    Archive
    """

    archive_view_class = views.WorkflowArchiveListView

    def get_archive_view_kwargs(self, **kwargs):
        return self.filter_kwargs(self.archive_view_class, **kwargs)

    @viewprop
    def archive_view(self):
        return self.archive_view_class.as_view(**self.get_archive_view_kwargs())

    @property
    def archive_path(self):
        return path("archive/", self.archive_view, name="archive")

    def get_context_data(self, request):
        inbox = Task.objects.inbox(self.flow_classes, request.user)

        queue = Task.objects.queue(self.flow_classes, request.user)

        return {
            "user_inbox": inbox,
            "user_queue": queue,
        }
