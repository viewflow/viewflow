from django.views import generic
from viewflow import flow

from . import models


class DecisionView(flow.TaskFormViewMixin, generic.CreateView):
    model = models.Decision
    fields = ['decision']

    def activation_done(self, form):
        self.object = form.save(commit=False)

        self.object.user = self.request.user
        self.object.process = self.activation.process
        self.object.save()

        self.activation.done()
