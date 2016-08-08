from django.conf.urls import url
from viewflow.flow import views
from .flows import HelloWorldFlow

urlpatterns = [
    url('^$', views.ProcessListView.as_view(flow_class=HelloWorldFlow), name='index'),
    url('^tasks/$', views.TaskListView.as_view(flow_class=HelloWorldFlow), name='tasks'),
    url('^queue/$', views.QueueListView.as_view(flow_class=HelloWorldFlow), name='queue'),
    url('^detail/(?P<process_pk>\d+)/$',
        views.DetailProcessView.as_view(flow_class=HelloWorldFlow), name='detail'),
    url('^action/cancel/(?P<process_pk>\d+)/$',
        views.CancelProcessView.as_view(flow_class=HelloWorldFlow), name='action_cancel'),
    HelloWorldFlow.instance.urls,
]
