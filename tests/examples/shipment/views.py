from django.http import HttpResponseRedirect
from django.views.generic import CreateView, UpdateView
from viewflow.flow.start import StartViewMixin
from viewflow.flow.view import TaskViewMixin
from examples.shipment.models import Shipment


class StartView(StartViewMixin, CreateView):
    model = Shipment
    fields = ['goods_tag']

    def form_valid(self, form):
        self.object = form.save()
        self.activation.process.created_by = self.request.user
        self.activation.process.shipment = self.object
        self.activation.done()
        return HttpResponseRedirect(self.get_success_url())


class ShipmentView(TaskViewMixin, UpdateView):
    def get_object(self):
        return self.activation.process.shipment
