import django

from django.conf.urls import include, url
from django.contrib import admin
from viewflow import views as viewflow

from examples.helloworld.flows import HelloWorldFlow
from examples.shipment.flows import ShipmentFlow
from examples.customnode.flows import DynamicSplitFlow


if django.VERSION < (1, 7):
    admin.autodiscover()

flow_classes = [HelloWorldFlow, ShipmentFlow, DynamicSplitFlow]


urlpatterns = [
    url(r'^$', viewflow.AllProcessListView.as_view(flow_classes=flow_classes), name="index"),
    url(r'^tasks/$', viewflow.AllTaskListView.as_view(flow_classes=flow_classes), name="tasks"),
    url(r'^queue/$', viewflow.AllQueueListView.as_view(flow_classes=flow_classes), name="queue"),

    # hello world
    url(r'^helloworld/', include([
        HelloWorldFlow.instance.urls,
        url('^$', viewflow.ProcessListView.as_view(), name='index'),
        url('^tasks/$', viewflow.TaskListView.as_view(), name='tasks'),
        url('^queue/$', viewflow.QueueListView.as_view(), name='queue'),
        url('^details/(?P<process_pk>\d+)/$', viewflow.ProcessDetailView.as_view(), name='details'),
        url('^action/cancel/(?P<process_pk>\d+)/$', viewflow.ProcessCancelView.as_view(), name='action_cancel'),
    ], namespace=HelloWorldFlow.instance.namespace), {'flow_cls': HelloWorldFlow}),

    # shipment
    url(r'^shipment/', include([
        ShipmentFlow.instance.urls,
        url('^$', viewflow.ProcessListView.as_view(), name='index'),
        url('^tasks/$', viewflow.TaskListView.as_view(), name='tasks'),
        url('^queue/$', viewflow.QueueListView.as_view(), name='queue'),
        url('^details/(?P<process_pk>\d+)/$', viewflow.ProcessDetailView.as_view(), name='details'),
    ], namespace=ShipmentFlow.instance.namespace), {'flow_cls': ShipmentFlow}),

    # dynamic split
    url(r'^dynamicsplit/', include([
        DynamicSplitFlow.instance.urls,
        url('^$', viewflow.ProcessListView.as_view(), name='index'),
        url('^tasks/$', viewflow.TaskListView.as_view(), name='tasks'),
        url('^queue/$', viewflow.QueueListView.as_view(), name='queue'),
        url('^details/(?P<process_pk>\d+)/$', viewflow.ProcessDetailView.as_view(), name='details'),
    ], namespace=DynamicSplitFlow.instance.namespace), {'flow_cls': DynamicSplitFlow}),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^', include('examples.website')),
]
