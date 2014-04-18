from django.conf.urls import patterns, url, include
from examples.shipment.flows import ShipmentFlow

urlpatterns = patterns('',  # NOQA
    url(r'^', include(ShipmentFlow.instance.urls)))
