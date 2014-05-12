from django.contrib import admin
from viewflow.admin import ProcessAdmin, TaskAdmin
from examples.shipment import models, flows


@admin.register(models.ShipmentProcess)
class ShipmentProcessAdmin(ProcessAdmin):
    list_display = ['pk', 'created_by', 'get_status_display', 'participants',
                    'is_normal_post', 'need_extra_insurance']
    list_display_links = ['pk', 'created_by']


@admin.register(models.ShipmentTask)
class ShipmentTaskAdmin(TaskAdmin):
    list_display = ['pk', 'created', 'get_status_display',
                    'owner', 'owner_permission', 'token',
                    'started', 'finished']
    list_display_links = ['pk', 'created']

    def get_queryset(self, request):
        qs = super(ShipmentTaskAdmin, self).get_queryset(request)
        return qs.filter(process__flow_cls=flows.ShipmentFlow)


@admin.register(models.Carrier)
class CarrierAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'is_default']


@admin.register(models.Insurance)
class InsuranceAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'cost']


@admin.register(models.Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['goods_tag', 'carrier', 'carrier_quote', 'insurance', 'package_tag']
