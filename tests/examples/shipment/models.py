from django.db import models
from django.conf import settings
from viewflow.models import Process


class Carrier(models.Model):
    DEFAULT = 'Default'

    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)

    def is_default(self):
        return self.name == Carrier.DEFAULT

    def __str__(self):
        return self.name


class Insurance(models.Model):
    company_name = models.CharField(max_length=50)
    cost = models.IntegerField()


class Shipment(models.Model):
    goods_tag = models.CharField(max_length=50)
    carrier = models.ForeignKey(Carrier, null=True)

    need_insurance = models.BooleanField(default=False)
    insurance = models.ForeignKey('Insurance', null=True)

    carrier_quote = models.IntegerField(blank=True, default=0)
    post_label = models.TextField(blank=True, null=True)

    package_tag = models.CharField(max_length=50)


class ShipmentProcess(Process):
    shipment = models.ForeignKey(Shipment, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)

    def is_normal_post(self):
        try:
            return self.shipment.carrier.is_default()
        except (Shipment.DoesNotExist, Carrier.DoesNotExist):
            return None

    def need_extra_insurance(self):
        try:
            return self.shipment.need_insurance
        except Shipment.DoesNotExist:
            return None

    class Meta:
        permissions = [
            ('can_start_request', 'Can start shipment request'),
            ('can_take_extra_insurance', 'Can take extra insurance'),
            ('can_package_goods', 'Can package goods'),
            ('can_move_package', 'Can move package')
        ]
