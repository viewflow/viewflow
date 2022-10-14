from django.http import HttpResponseRedirect
from django.views import generic
from django.utils.translation import gettext_lazy as _

from . import mixins


class CreateProcessView(
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.UpdateView
):
    """Default view to start a process"""

    success_message = _('Process {process} has been started.')
    template_filename = 'start.html'

    def get_object(self):
        """Return the process for the task activation."""
        return self.request.activation.process

    def form_valid(self, form):
        """If the form is valid, save the associated model and finish the task."""
        self.object = form.save()
        self.request.activation.execute()
        return HttpResponseRedirect(self.get_success_url())


class CreateArtifactView(
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.CreateView
):
    template_filename = 'start.html'

    def form_valid(self, form):
        self.object = form.save()
        self.request.activation.process.artifact = self.object
        self.request.activation.execute()
        return HttpResponseRedirect(self.get_success_url())
