from django.contrib import messages
from django.views import generic
from django.utils.translation import gettext_lazy as _
from . import mixins


class IndexTaskView(generic.RedirectView):
    """Redirect to the task detail."""

    def get_redirect_url(self, *args, **kwargs):
        activation = self.request.activation

        return activation.flow_task.reverse(
            "detail", args=[activation.process.pk, activation.task.pk]
        )


class UserIndexTaskView(generic.RedirectView):
    """Redirect for a flow.View node."""

    def get_redirect_url(self, *args, **kwargs):
        activation = self.request.activation
        task = activation.task
        flow_task = activation.flow_task

        if activation.start.can_proceed() and flow_task.can_execute(
            self.request.user, task
        ):
            return flow_task.reverse("execute", args=[task.process_id, task.pk])

        if activation.assign.can_proceed() and flow_task.can_assign(
            self.request.user, task
        ):
            return flow_task.reverse("assign", args=[task.process_id, task.pk])

        if flow_task.can_view(self.request.user, task):
            return flow_task.reverse("detail", args=[task.process_id, task.pk])

        messages.success(
            self.request, _("You have no rights to view this task"), fail_silently=True
        )

        return "/"


class DetailTaskView(mixins.TaskViewTemplateNames, generic.TemplateView):
    """
    Default detail view for the flow task.

    Get confirmation from user, assigns task and redirects to task pages.
    """

    template_filename = "task_detail.html"

    def get_actions(self):
        activation = self.request.activation
        return activation.flow_task.get_available_actions(activation, self.request.user)


class DetailProcessView(generic.DetailView):  # todo permission
    """Detail for process."""

    flow_class = None
    context_object_name = "process"
    pk_url_kwarg = "process_pk"

    def get_template_names(self):
        """List of template names to be used for a process detail page.

        If `template_name` is None, default value is::

            [<app_label>/<flow_label>/process_detail.html,
             'viewflow/workflow/process_detail.html']
        """
        if self.template_name is None:
            opts = self.flow_class.instance

            return (
                "{}/{}/process_detail.html".format(opts.app_label, opts.flow_label),
                "viewflow/workflow/process_detail.html",
            )
        else:
            return [self.template_name]

    def get_context_data(self, **kwargs):
        """Context for a detail view.

        :keyword process: a Process instance
        :keyword task_list: List of tasks of the process
        """
        context = super(DetailProcessView, self).get_context_data(**kwargs)
        context["task_list"] = context["process"].task_set.all().order_by("created")
        return context

    def get_queryset(self):
        """Return the `QuerySet` that will be used to look up the process."""
        if self.queryset is None:
            return self.flow_class.process_class._default_manager.all()
        return self.queryset.all()


class DetailSubprocessView(DetailTaskView):
    def get_template_names(self):
        flow_task = self.activation.flow_task
        opts = self.activation.flow_task.flow_class.instance

        return (
            "{}/{}/{}_detail.html".format(
                opts.app_label, opts.flow_label, flow_task.name
            ),
            "{}/{}/subprocess_detail.html".format(opts.app_label, opts.flow_label),
            "viewflow/workflow/subprocess_detail.html",
        )
