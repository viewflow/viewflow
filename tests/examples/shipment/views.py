import extra_views
from django.views import generic
from viewflow import views as flow_views
from material import LayoutMixin, Layout, Fieldset, Inline, Row, Span2, Span5, Span7

from .models import Shipment, ShipmentItem, Insurance


class ItemInline(extra_views.InlineFormSet):
    model = ShipmentItem
    fields = ['name', 'quantity']


class StartView(LayoutMixin,
                flow_views.StartViewMixin,
                extra_views.NamedFormsetsMixin,
                extra_views.CreateWithInlinesView):
    model = Shipment
    layout = Layout(
        Row('shipment_no'),
        Fieldset('Customer Details',
                 Row('first_name', 'last_name', 'email'),
                 Row('phone')),
        Fieldset('Address',
                 Row(Span7('address'), Span5('zipcode')),
                 Row(Span5('city'), Span2('state'), Span5('country'))),
        Inline('Shipment Items', ItemInline),
    )

    def activation_done(self, form, inlines):
        self.object = form.save()
        for formset in inlines:
            formset.save()

        self.activation.process.created_by = self.request.user
        self.activation.process.shipment = self.object
        self.activation.done()


class ShipmentView(flow_views.TaskViewMixin, generic.UpdateView):
    def get_object(self):
        return self.activation.process.shipment


class InsuranceView(flow_views.TaskViewMixin, generic.CreateView):
    model = Insurance
    fields = ['company_name', 'cost']

    def activation_done(self, form):
        shipment = self.activation.process.shipment
        shipment.insurance = self.object
        shipment.save(update_fields=['insurance'])
        self.activation.done()
