from django.conf.urls import include, url
from django.test import TestCase

from viewflow import views as viewflow
from viewflow.test import FlowTest

from .flows import HelloWorldFlow


class HelloWorldFlowTests(TestCase):
    urls = __name__
    fixtures = ['helloworld/default_data.json']

    def test_normal_flow_succeed(self):
        with FlowTest(HelloWorldFlow) as flow:
            # The `employee` starts process
            flow.Task(HelloWorldFlow.start).User('helloworld/employee') \
                .Execute({'text': 'Test Request'}) \
                .Assert(lambda p: p.created is not None)

            # The `manager` approve the request
            flow.Task(HelloWorldFlow.approve).User('helloworld/manager') \
                .Execute({'approved': True}) \
                .Assert(lambda p: p.finished is None)

            # Send hello request succed
            flow.Task(HelloWorldFlow.send) \
                .Execute() \
                .Assert(lambda p: p.finished is not None)


urlpatterns = [
    url(r'^helloworld/', include([
        HelloWorldFlow.instance.urls,
        url('^$', viewflow.ProcessListView.as_view(), name='index'),
        url('^tasks/$', viewflow.TaskListView.as_view(), name='tasks'),
        url('^queue/$', viewflow.QueueListView.as_view(), name='queue'),
        url('^details/(?P<process_pk>\d+)/$', viewflow.ProcessDetailView.as_view(), name='details'),
        url('^action/cancel/(?P<process_pk>\d+)/$', viewflow.ProcessCancelView.as_view(), name='action_cancel'),
    ], namespace=HelloWorldFlow.instance.namespace), {'flow_cls': HelloWorldFlow}),
]
