from django.views.generic import CreateView, UpdateView
from viewflow.flow.start import StartInlinesViewMixin
from viewflow.flow.view import TaskFormViewMixin
from extra_views import InlineFormSet, CreateWithInlinesView
from viewflow.viewform import Layout, Fieldset, Inline, Row, Span2, Span5, Span7

from .models import Shipment, ShipmentItem, Insurance


class ShipmentItemInline(InlineFormSet):
    model = ShipmentItem


class StartView(StartInlinesViewMixin, CreateWithInlinesView):
    model = Shipment
    fields = ['shipment_no', 'first_name', 'last_name', 'email',
              'address', 'city', 'state', 'zipcode', 'country',
              'phone']
    layout = Layout(
        Row('shipment_no'),
        Row('first_name', 'last_name', 'email'),
        Row('phone'),
        Fieldset('Address',
                 Row(Span7('address'), Span5('zipcode')),
                 Row(Span5('city'), Span2('state'), Span5('country'))),
        Inline('Shipment Items', 'Items'),
    )

    inlines = [ShipmentItemInline]
    inlines_names = ["Items"]

    def activation_done(self, form, inlines):
        self.object = form.save()
        for formset in inlines:
            formset.save()

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
