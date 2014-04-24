from django.db import models
from django.conf import settings
from viewflow.models import Process


class Carrier(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=15)


class Insurance(models.Model):
    company_name = models.CharField(max_length=50)
    cost = models.IntegerField()


class Shipment(models.Model):
    goods_tag = models.CharField(max_length=50)
    carrier = models.ForeignKey(Carrier, blank=True, null=True)

    need_insurance = models.BooleanField(default=False)
    insurance = models.ForeignKey('Insurance', blank=True, null=True)

    carrier_quote = models.IntegerField(blank=True, default=0)
    post_label = models.TextField(blank=True, null=True)

    package_tag = models.CharField(max_length=50)


class ShipmentProcess(Process):
    shipment = models.ForeignKey(Shipment, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)

    def is_normal_post():
        raise NotImplementedError

    def need_extra_insurance():
        raise NotImplementedError

    class Meta:
        permissions = [
            ('can_start_request', 'Can start shipment request'),
            ('can_take_extra_insurance', 'Can take extra insurance'),
            ('can_package_goods', 'Can package goods'),
            ('can_move_package', 'Can move package')
        ]
