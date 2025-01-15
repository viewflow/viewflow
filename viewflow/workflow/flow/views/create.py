from django.http import HttpResponseRedirect
from django.views import generic
from django.utils.translation import gettext_lazy as _
from viewflow.forms import FormAjaxCompleteMixin, FormDependentSelectMixin
from viewflow.views import FormLayoutMixin

from . import mixins


class CreateProcessView(
    FormLayoutMixin,
    FormAjaxCompleteMixin,
    FormDependentSelectMixin,
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.UpdateView,
):
    """Default view to start a process"""

    success_message = _("Process {process} has been started.")
    template_filename = "start.html"

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


class CreateArtifactView(
    FormLayoutMixin,
    FormAjaxCompleteMixin,
    FormDependentSelectMixin,
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.CreateView,
):
    template_filename = "start.html"

    def form_valid(self, form):
        self.object = form.save()
        self.request.activation.process.artifact = self.object
        self.request.activation.execute()
        return HttpResponseRedirect(self.get_success_url())
