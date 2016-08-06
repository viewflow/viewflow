from django.conf.urls import url
from viewflow.flow import views
from .flows import DynamicSplitFlow


urlpatterns = [
    url('^$', views.ProcessListView.as_view(flow_class=DynamicSplitFlow), name='index'),
    url('^tasks/$', views.TaskListView.as_view(flow_class=DynamicSplitFlow), name='tasks'),
    url('^queue/$', views.QueueListView.as_view(flow_class=DynamicSplitFlow), name='queue'),
    url('^details/(?P<process_pk>\d+)/$',
        views.DetailProcessView.as_view(flow_class=DynamicSplitFlow), name='details'),
    DynamicSplitFlow.instance.urls,
]
