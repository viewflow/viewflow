import django
from django.conf.urls import patterns, include, url
from django.contrib import admin
from viewflow import views as viewflow

from tests.examples.helloworld.flows import HelloWorldFlow
from tests.examples.shipment.flows import ShipmentFlow
from tests.examples.customnode.flows import DynamicSplitFlow


if django.VERSION < (1, 7):
    admin.autodiscover()


flow_classes = [HelloWorldFlow, ShipmentFlow, DynamicSplitFlow]

urlpatterns = patterns(
    '',
    url(r'^$', viewflow.AllProcessListView.as_view(flow_classes=flow_classes), name="index"),
    url(r'^tasks/$', viewflow.AllTaskListView.as_view(flow_classes=flow_classes), name="tasks"),
    url(r'^queue/$', viewflow.AllQueueListView.as_view(flow_classes=flow_classes), name="queue"),

    # hello world
    url(r'^helloworld/', include([
        url('^$', viewflow.ProcessListView.as_view(flow_cls=HelloWorldFlow), name='index')
    ], namespace=HelloWorldFlow._meta.urls_namespace, app_name=HelloWorldFlow._meta.namespace)),
    url(r'^helloworld/flow/', include(HelloWorldFlow.instance.urls)),

    # shipment
    url(r'^shipment/', include(ShipmentFlow.instance.urls)),

    # dynamic split
    url(r'^dynamicsplit/', include(DynamicSplitFlow.instance.urls)),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^', include('tests.examples.website')),
)
