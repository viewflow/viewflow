from django.http import HttpResponseRedirect
from django.views.generic import CreateView, UpdateView
from viewflow.flow.start import StartViewMixin
from viewflow.flow.view import TaskViewMixin
from examples.shipment.models import Shipment, Insurance


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


class InsuranceView(TaskViewMixin, CreateView):
    model = Insurance
    fields = ['company_name', 'cost']

    def get_object(self):
        if self.activation.process.shipment.insurance_id:
            return self.activation.process.shipment.insurance
        else:
            return Insurance()

    def form_valid(self, form):
        self.object = form.save()

        shipment = self.activation.process.shipment
        shipment.insurance = self.object
        shipment.save(update_fields=['insurance'])
        self.activation.done()

        return HttpResponseRedirect(self.get_success_url())
