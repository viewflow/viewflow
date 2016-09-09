from django.conf.urls import include, url
from django.test import TestCase

from viewflow.flow import routers
from viewflow.test import FlowTest

from .flows import HelloWorldFlow


class Test(TestCase):
    fixtures = ['helloworld/default_data.json']

    def test_normal_flow_succeed(self):
        with FlowTest(HelloWorldFlow, namespace='helloworld') as flow:
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
    url(r'^helloworld/', include(routers.FlowRouter(HelloWorldFlow).urls, namespace='helloworld')),
]

try:
    from django.test import override_settings
    Test = override_settings(ROOT_URLCONF=__name__)(Test)
except ImportError:
    """
    django 1.6
    """
    Test.urls = __name__
