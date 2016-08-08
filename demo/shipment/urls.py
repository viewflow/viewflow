from django.conf.urls import url
from viewflow.flow import views
from .flows import ShipmentFlow

urlpatterns = [
    url('^$', views.ProcessListView.as_view(flow_class=ShipmentFlow), name='index'),
    url('^tasks/$', views.TaskListView.as_view(flow_class=ShipmentFlow), name='tasks'),
    url('^queue/$', views.QueueListView.as_view(flow_class=ShipmentFlow), name='queue'),
    url('^detail/(?P<process_pk>\d+)/$',
        views.DetailProcessView.as_view(flow_class=ShipmentFlow), name='detail'),
    ShipmentFlow.instance.urls,
]
