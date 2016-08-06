from textwrap import dedent
from django.test import TestCase

from viewflow import base, flow
from viewflow.base import this


class Test(TestCase):
    def test_flowmeta_helpers(self):
        flow_meta = base.FlowMeta('tests', type('StubFlow', (object,), {}), {})

        self.assertEqual(flow_meta.flow_label, 'test_base/stub')

    def test_flowmetaclass_setup_succeed(self):
        class TestFlow(base.Flow):
            """
            The Test Flow

            Flow docstring should be splitted, first string goes to
            the process_title and rest used as flow description
            """
            start = flow.Start(lambda request: None).Next(this.end)
            end = flow.End()

        # Singleton instance
        self.assertEqual(TestFlow.instance, TestFlow.instance)
        self.assertTrue(isinstance(TestFlow.instance, TestFlow))

        # Node initialized
        self.assertEqual(TestFlow.start.name, 'start')
        self.assertEqual(TestFlow.start.flow_class, TestFlow)
        self.assertEqual(TestFlow.end.name, 'end')
        self.assertEqual(TestFlow.end.flow_class, TestFlow)

        # Node interlinks are resolved
        self.assertEqual(TestFlow.start._next, TestFlow.end)
        self.assertEqual([x.src for x in TestFlow.start._incoming()], [])
        self.assertEqual([x.dst for x in TestFlow.start._outgoing()], [TestFlow.end])
        self.assertEqual([x.src for x in TestFlow.end._incoming()], [TestFlow.start])
        self.assertEqual([x.dst for x in TestFlow.end._outgoing()], [])

        # Process documentation
        self.assertEqual(TestFlow.process_title, 'The Test Flow')
        self.assertEqual(TestFlow.process_description, dedent("""
            Flow docstring should be splitted, first string goes to
            the process_title and rest used as flow description
        """).strip())
