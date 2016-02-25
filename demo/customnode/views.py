from django.views import generic
from django.http import HttpResponseRedirect

from viewflow.views import task

from . import models


class DecisionView(task.TaskViewMixin, generic.CreateView):
    model = models.Decision
    fields = ['decision']

    def form_valid(self, form):
        self.object = form.save(commit=False)

        self.object.user = self.request.user
        self.object.process = self.activation.process
        self.object.save()

        self.activation.done()
        self.message_complete()

        return HttpResponseRedirect(self.get_success_url())
