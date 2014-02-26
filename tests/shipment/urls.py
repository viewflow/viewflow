from django.conf.urls import patterns, url, include
from shipment.flows import ShipmentFlow

urlpatterns = patterns('',  # NOQA
    url(r'^flow/', include(ShipmentFlow.instance.urls)))


"""
urlpatterns = patterns('shipment.views',
    url(r'shipment_type/(?P<act_id>\d+)/$', 'shipment_type', {'flow_task': ShipmentFlow.shipment_type}),  # NOQA
    url(r'package_goods/(?P<act_id>\d+)/$', 'package_goods', {'flow_task': ShipmentFlow.package_goods}),
    url(r'check_insurance/(?P<act_id>\d+)/$', 'check_insurance', {'flow_task': ShipmentFlow.check_insurance}),
    url(r'request_quotes/(?P<act_id>\d+)/$', 'request_quotes', {'flow_task': ShipmentFlow.request_quotes}),
    url(r'take_extra_insurance/(?P<act_id>\d+)/$', 'take_extra_insurance',
        {'flow_task': ShipmentFlow.take_extra_insurance}),
    url(r'fill_post_label/(?P<act_id>\d+)/$', 'fill_post_label', {'flow_task': ShipmentFlow.fill_post_label}),
    url(r'assign_carrier/(?P<act_id>\d+)/$', 'assign_carrier', {'flow_task': ShipmentFlow.assign_carrier}),
    url(r'move_package/(?P<act_id>\d+)/$', 'move_package', {'flow_task': ShipmentFlow.move_package}),
)
"""
