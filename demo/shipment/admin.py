from django.contrib import admin

from . import models


class CarrierAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">local_shipping</i>'
    list_display = ['name', 'phone', 'is_default']


class InsuranceAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">account_balance_wallet</i>'
    list_display = ['company_name', 'cost']


class ShipmentAdmin(admin.ModelAdmin):
    icon = '<i class="material-icons">shopping_cart</i>'
    list_display = ['shipment_no', 'carrier', 'carrier_quote', 'insurance', 'package_tag']


admin.site.register(models.Carrier, CarrierAdmin)
admin.site.register(models.Insurance, InsuranceAdmin)
admin.site.register(models.Shipment, ShipmentAdmin)
