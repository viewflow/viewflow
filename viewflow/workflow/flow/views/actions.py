from django import forms
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import generic

from viewflow.views import BaseBulkActionView
from viewflow.workflow.models import Task
from viewflow.workflow.status import PROCESS, STATUS
from . import mixins


class AssignTaskView(
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.FormView,
):
    """
    Default assign view for flow task.

    Get confirmation from user, assigns task and redirects to task pages
    """

    form_class = forms.Form
    template_filename = "task_assign.html"
    success_message = _("Task {task} has been assigned.")

    def form_valid(self, *args, **kwargs):
        """If the form is valid, save the associated model and finish the task."""
        self.request.activation.assign(self.request.user)
        return super().form_valid(*args, **kwargs)


class UnassignTaskView(
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.FormView,
):
    """
    Default unassign view for flow task.

    Get confirmation from user, and unassign task
    """

    form_class = forms.Form
    template_filename = "task_unassign.html"
    success_message = _("Task {task} has been unassigned.")

    def form_valid(self, *args, **kwargs):
        """If the form is valid, save the associated model and unassign the task."""
        self.request.activation.unassign()
        return super().form_valid(*args, **kwargs)


class CancelTaskView(
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.FormView,
):
    """
    Default unassign view for flow task.

    Get confirmation from user, and unassign task
    """

    form_class = forms.Form
    template_filename = "task_cancel.html"
    success_message = _("Task {task} has been canceled.")

    def form_valid(self, *args, **kwargs):
        """If the form is valid, save the associated model and cancels the task."""
        self.request.activation.cancel()
        return super().form_valid(*args, **kwargs)


class UndoTaskView(
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.FormView,
):
    """
    Default undo view for flow task.

    Get confirmation from user, and undo the task
    """

    form_class = forms.Form
    template_filename = "task_undo.html"
    success_message = _("Task {task} has been undone.")

    def form_valid(self, *args, **kwargs):
        """If the form is valid, save the associated model and undo the task."""
        self.request.activation.undo()
        return super().form_valid(*args, **kwargs)


class ReviveTaskView(
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.FormView,
):
    """
    Default review view for flow task.

    Get confirmation from user, and revives task
    """

    form_class = forms.Form
    template_filename = "task_revive.html"
    success_message = _("Task {task} has been revived.")

    def form_valid(self, *args, **kwargs):
        """If the form is valid, save the associated model and revives the task."""
        self.request.activation.revive()
        return super().form_valid(*args, **kwargs)


class CancelProcessView(mixins.ProcessViewTemplateNames, generic.DetailView):
    context_object_name = "process"
    flow_class = None
    pk_url_kwarg = "process_pk"
    template_filename = "process_cancel.html"

    def get_queryset(self):
        """Flow processes."""
        return self.flow_class.process_class._default_manager.all()

    @cached_property
    def active_activations(self):
        return [
            task.flow_task.activation_class(task)
            for task in self.object.task_set.exclude(
                status__in=[STATUS.DONE, STATUS.CANCELED]
            )
        ]

    def post(self, request, *args, **kwargs):
        """Cancel active tasks and the process."""
        self.object = self.get_object()

        if self.object.status in [PROCESS.DONE, PROCESS.CANCELED]:
            messages.add_message(
                self.request,
                messages.ERROR,
                _("Process #{self.object.pk} can not be canceled."),
                fail_silently=True,
            )
            return HttpResponseRedirect('../')
        elif "_cancel_process" in request.POST:
            self.object.flow_class.instance.cancel(self.object)
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _("Process #{self.object.pk} has been canceled."),
                fail_silently=True,
            )
            return HttpResponseRedirect('../')
        else:
            return self.get(request, *args, **kwargs)


class BulkUnassignTasksActionView(BaseBulkActionView):
    model = Task
    template_name = "viewflow/workflow/tasks_unassign.html"
    template_name_suffix = "s_unassign"

    def form_valid(self, form):
        with transaction.atomic():
            for task in self.get_queryset():
                with task.activation() as activation:
                    activation.unassign()
        self.message_user()
        return HttpResponseRedirect(self.get_success_url())

    def message_user(self):
        message = "Tasks was unassigned"
        messages.add_message(
            self.request, messages.SUCCESS, message, fail_silently=True
        )


class BulkAssignTasksActionView(BaseBulkActionView):
    model = Task
    template_name = "viewflow/workflow/tasks_assign.html"
    template_name_suffix = "s_assign"

    def form_valid(self, form):
        with transaction.atomic():
            for task in self.get_queryset():
                with task.activation() as activation:
                    activation.assign(self.request.user)
        self.message_user()
        return HttpResponseRedirect(self.get_success_url())

    def message_user(self):
        message = "Tasks was assigned"
        messages.add_message(
            self.request, messages.SUCCESS, message, fail_silently=True
        )
