from django.conf.urls import patterns, url, include
from .flows import ShipmentFlow

urlpatterns = patterns('',  # NOQA
    url(r'^', include(ShipmentFlow.instance.urls)))
