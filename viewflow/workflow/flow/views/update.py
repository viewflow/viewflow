from django.http import HttpResponseRedirect
from django.views import generic
from django.utils.translation import gettext_lazy as _

from . import mixins


class UpdateProcessView(
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.UpdateView
):
    """Default view to update a process"""

    success_message = _('Task {task} has been completed.')
    template_filename = 'task.html'

    def get_object(self):
        """Return the process for the task activation."""
        return self.request.activation.process

    def form_valid(self, form):
        """If the form is valid, save the associated model and finish the task."""
        self.object = form.save()
        self.request.activation.execute()
        return HttpResponseRedirect(self.get_success_url())


class UpdateArtifactView(
    mixins.SuccessMessageMixin,
    mixins.TaskSuccessUrlMixin,
    mixins.TaskViewTemplateNames,
    generic.UpdateView
):
    success_message = _('Task {task} has been completed.')
    template_filename = 'task.html'

    def get_object(self):
        """Return the process for the task activation."""
        return self.request.activation.process.artifact

    def form_valid(self, form):
        """If the form is valid, save the associated model and finish the task."""
        self.object = form.save()
        self.request.activation.execute()
        return HttpResponseRedirect(self.get_success_url())
