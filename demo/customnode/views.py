from django.views import generic
from django.http import HttpResponseRedirect

from viewflow.flow.views import FlowMixin

from . import models


class DecisionView(FlowMixin, generic.CreateView):
    model = models.Decision
    fields = ['decision']

    def form_valid(self, form):
        self.object = form.save(commit=False)

        self.object.user = self.request.user
        self.object.process = self.activation.process
        self.object.save()

        self.activation.done()
        self.success('Task {task} has been completed.')

        return HttpResponseRedirect(self.get_success_url())
