from django.core.exceptions import PermissionDenied
from django.forms.models import modelform_factory, inlineformset_factory
from django.views import generic
from django.shortcuts import render, redirect
from viewflow.flow import flow_start_view
from viewflow.flow.views import ViewMixin, get_next_task_url


from .models import Shipment, ShipmentItem, Insurance


@flow_start_view()
def start_view(request, activation):
    form_cls = modelform_factory(Shipment, fields=[
        'shipment_no', 'first_name', 'last_name',
        'email', 'phone', 'address', 'zipcode',
        'city', 'state', 'country'])

    formset_cls = inlineformset_factory(Shipment, ShipmentItem, fields=[
        'name', 'quantity'], can_delete=False)

    if not activation.has_perm(request.user):
        raise PermissionDenied
    activation.prepare(request.POST or None, user=request.user)

    form = form_cls(request.POST or None)
    formset = formset_cls(request.POST or None)

    is_valid = all([form.is_valid(), formset.is_valid()])
    if is_valid:
        shipment = form.save()
        activation.process.shipment = shipment
        for item in formset.save(commit=False):
            item.shipment = shipment
            item.save()
        activation.done()
        return redirect(get_next_task_url(request, activation.process))

    return render(request, 'shipment/shipment/start.html', {
        'activation': activation,
        'form': form,
        'formset': formset
    })


class ShipmentView(ViewMixin, generic.UpdateView):
    def get_object(self):
        return self.activation.process.shipment


class InsuranceView(ViewMixin, generic.CreateView):
    model = Insurance
    fields = ['company_name', 'cost']

    def activation_done(self, form):
        shipment = self.activation.process.shipment
        shipment.insurance = self.object
        shipment.save(update_fields=['insurance'])
        self.activation.done()
