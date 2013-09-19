from django.test import TestCase
from viewflow import flow, Flow


def perform_task(request, act_id):
    raise NotImplementedError


class TestFlow(Flow):
    start = flow.Start() \
        .Activate('task')
    task = flow.View(perform_task)\
        .Next('end')
    end = flow.End()


class TestFlowConformance(TestCase):
    def test_flow_meta_creation_succeed(self):
        self.assertTrue(hasattr(TestFlow, '_meta'))

    def test_task_names_established(self):
        names = set(node.name for node in TestFlow._meta.nodes())
        self.assertEqual(set(['start', 'task', 'end']), names)

    def test_flow_interlinks_resolved(self):
        for node in TestFlow._meta.nodes():
            for edge in node._outgoing():
                self.assertTrue(isinstance(edge.dst, flow._Node))
            for edge in node._incoming():
                self.assertTrue(isinstance(edge.dst, flow._Node))
