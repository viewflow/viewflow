from django.views.generic import CreateView, UpdateView
from viewflow.flow.start import StartFormViewMixin
from viewflow.flow.view import TaskFormViewMixin
from examples.shipment.models import Shipment, Insurance


class StartView(StartFormViewMixin, CreateView):
    model = Shipment
    fields = ['goods_tag']

    def activation_done(self, form):
        self.object = form.save()
        self.activation.process.created_by = self.request.user
        self.activation.process.shipment = self.object
        self.activation.done()


class ShipmentView(TaskFormViewMixin, UpdateView):
    def get_object(self):
        return self.activation.process.shipment


class InsuranceView(TaskFormViewMixin, CreateView):
    model = Insurance
    fields = ['company_name', 'cost']

    def activation_done(self, form):
        self.object = form.save()

        shipment = self.activation.process.shipment
        shipment.insurance = self.object
        shipment.save(update_fields=['insurance'])
        self.activation.done()
