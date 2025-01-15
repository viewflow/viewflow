from django.http import HttpResponseRedirect
from django.views import generic
from django.utils.translation import gettext_lazy as _
from viewflow.views import FormLayoutMixin
from viewflow.forms import FormAjaxCompleteMixin, FormDependentSelectMixin
from . import mixins


class UpdateProcessView(
    FormLayoutMixin,
    FormAjaxCompleteMixin,
    FormDependentSelectMixin,
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.UpdateView,
):
    """Default view to update a process"""

    success_message = _("Task {task} has been completed.")
    template_filename = "task.html"

    def get_object(self):
        """Return the process for the task activation."""
        return self.request.activation.process

    def form_valid(self, form):
        """If the form is valid, save the associated model and finish the task."""
        self.object = form.save()
        if "seed" in form.cleaned_data:
            self.object.seed = form.cleaned_data["seed"]
        if "artifact" in form.cleaned_data:
            self.object.artifact = form.cleaned_data["artifact"]
        self.request.activation.execute()
        return HttpResponseRedirect(self.get_success_url())


class UpdateArtifactView(
    FormLayoutMixin,
    FormAjaxCompleteMixin,
    FormDependentSelectMixin,
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.UpdateView,
):
    success_message = _("Task {task} has been completed.")
    template_filename = "task.html"

    def get_object(self):
        """Return the process for the task activation."""
        return self.request.activation.process.artifact

    def form_valid(self, form):
        """If the form is valid, save the associated model and finish the task."""
        self.object = form.save()
        self.request.activation.execute()
        return HttpResponseRedirect(self.get_success_url())
