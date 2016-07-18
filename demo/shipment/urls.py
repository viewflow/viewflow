from django.conf.urls import url
from viewflow.flow import views
from .flows import ShipmentFlow

urlpatterns = [
    url('^$', views.ProcessListView.as_view(flow_cls=ShipmentFlow), name='index'),
    url('^tasks/$', views.TaskListView.as_view(flow_cls=ShipmentFlow), name='tasks'),
    url('^queue/$', views.QueueListView.as_view(flow_cls=ShipmentFlow), name='queue'),
    url('^details/(?P<process_pk>\d+)/$',
        views.DetailProcessView.as_view(flow_cls=ShipmentFlow), name='detail'),
    ShipmentFlow.instance.urls,
]
