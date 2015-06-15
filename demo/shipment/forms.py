from material.forms import SuperModelForm, InlineFormSetField

from .models import Shipment, ShipmentItem


class ShipmentForm(SuperModelForm):
    items = InlineFormSetField(
        Shipment, ShipmentItem,
        fields=['name', 'quantity'], can_delete=False)

    class Meta:
        model = Shipment
        fields = [
            'shipment_no', 'first_name', 'last_name',
            'email', 'phone', 'address', 'zipcode',
            'city', 'state', 'country'
        ]
