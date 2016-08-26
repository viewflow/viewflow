import django

from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth
from viewflow.flow import views as viewflow

from .helloworld.flows import HelloWorldFlow
from .shipment.flows import ShipmentFlow
from .customnode.flows import DynamicSplitFlow


if django.VERSION < (1, 7):
    admin.autodiscover()

flows = {
    'helloworld': HelloWorldFlow,
    'shipment': ShipmentFlow,
    'split': DynamicSplitFlow
}


urlpatterns = [
    url(r'^$', viewflow.AllProcessListView.as_view(ns_map=flows), name="index"),
    url(r'^tasks/$', viewflow.AllTaskListView.as_view(ns_map=flows), name="tasks"),
    url(r'^queue/$', viewflow.AllQueueListView.as_view(ns_map=flows), name="queue"),

    url(r'^helloworld/', include('demo.helloworld.urls', namespace='helloworld')),
    url(r'^shipment/', include('demo.shipment.urls', namespace='shipment')),
    url(r'^split/', include('demo.customnode.urls', namespace='split')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', auth.login, name='login'),
    url(r'^accounts/logout/$', auth.logout, name='logout'),
    url(r'^', include('demo.website')),
]
