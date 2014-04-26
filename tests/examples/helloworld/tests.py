from django.test import TestCase
from viewflow.test import FlowTest
from examples.helloworld.flows import HelloWorldFlow


class HelloWorldFlowTests(TestCase):
    def test_normal_flow_succeed(self):
        with FlowTest(HelloWorldFlow) as flow:
            # The `employee` starts process
            flow.Task(HelloWorldFlow.start).User('helloworld/employee') \
                .Execute() \
                .Assert(lambda p: p.created is not None)

            # The `employee` grabs hello_request task and excutes it
            flow.Task(HelloWorldFlow.hello_request).User('helloworld/employee') \
                .Execute({'text': 'Test Request'}) \
                .Assert(lambda p: p.text == 'Test Request')

            # The `manager` approve the request
            flow.Task(HelloWorldFlow.approve).User('helloworld/manager') \
                .Execute({'approved': True}) \
                .Assert(lambda p: p.finished is None)

            # Send hello request succed
            flow.Task(HelloWorldFlow.send) \
                .Execute() \
                .Assert(lambda p: p.finished is not None)
