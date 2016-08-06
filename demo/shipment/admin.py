from django.contrib import admin
from viewflow.admin import ProcessAdmin, TaskAdmin
from . import models, flows


class ShipmentProcessAdmin(ProcessAdmin):
    list_display = ['pk', 'created_by', 'status', 'participants',
                    'is_normal_post', 'need_extra_insurance']
    list_display_links = ['pk', 'created_by']


class ShipmentTaskAdmin(TaskAdmin):
    list_display = ['pk', 'created', 'status',
                    'owner', 'owner_permission', 'token',
                    'started', 'finished']
    list_display_links = ['pk', 'created']

    def get_queryset(self, request):
        qs = super(ShipmentTaskAdmin, self).get_queryset(request)
        return qs.filter(process__flow_class=flows.ShipmentFlow)


class CarrierAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'is_default']


class InsuranceAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'cost']


class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['shipment_no', 'carrier', 'carrier_quote', 'insurance', 'package_tag']


admin.site.register(models.ShipmentProcess, ShipmentProcessAdmin)
admin.site.register(models.ShipmentTask, ShipmentTaskAdmin)
admin.site.register(models.Carrier, CarrierAdmin)
admin.site.register(models.Insurance, InsuranceAdmin)
admin.site.register(models.Shipment, ShipmentAdmin)
