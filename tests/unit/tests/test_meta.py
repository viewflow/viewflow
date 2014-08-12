from django.test import TestCase
from ..flows import SingleTaskFlow


class TestMetaApi(TestCase):
    """
    Basic flow class API
    """
    def test_flow_meta_creation_succeed(self):
        self.assertTrue(hasattr(SingleTaskFlow, '_meta'))

    def test_task_names_established(self):
        names = set(node.name for node in SingleTaskFlow._meta.nodes())
        self.assertEqual(set(['start', 'task', 'end']), names)

    def test_get_node_by_name_succeed(self):
        self.assertEqual(SingleTaskFlow.start, SingleTaskFlow._meta.node('start'))
        self.assertEqual(SingleTaskFlow.task, SingleTaskFlow._meta.node('task'))
        self.assertEqual(SingleTaskFlow.end, SingleTaskFlow._meta.node('end'))

    def test_namespace_resolved(self):
        self.assertEqual('unit', SingleTaskFlow._meta.app_label)
        self.assertEqual('unit/singletask', SingleTaskFlow._meta.namespace)


class TestMetaConstruction(TestCase):
    def assertEdges(self, edges, expected_data):
        for edge in edges:
            for expected_src, expected_dst in expected_data:
                if edge.src == expected_src and edge.dst == expected_dst:
                    expected_data.remove([expected_src, expected_dst])
                    break
            else:
                self.fail('Edge {}->{} is unexpected'.format(edge.src.name, edge.dst.name))

        if expected_data:
            message = "Edges not found {}".format(
                '\n'.join("{} -> {}".format(
                    data[0].name, data[1].name) for data in expected_data))
            self.fail(' {}'.format(message))

    def test_flow_interlinks_resolved(self):
        # start
        self.assertEdges(
            SingleTaskFlow.start._outgoing(),
            [[SingleTaskFlow.start, SingleTaskFlow.task]])

        self.assertEdges(SingleTaskFlow.start._incoming(), [])

        # task
        self.assertEdges(
            SingleTaskFlow.task._outgoing(),
            [[SingleTaskFlow.task, SingleTaskFlow.end]])

        self.assertEdges(
            SingleTaskFlow.task._incoming(),
            [[SingleTaskFlow.start, SingleTaskFlow.task]])

        # end
        self.assertEdges(SingleTaskFlow.end._outgoing(), [])

        self.assertEdges(
            SingleTaskFlow.end._incoming(),
            [[SingleTaskFlow.task, SingleTaskFlow.end]])

    def test_instance_is_singleton(self):
        self.assertEqual(id(SingleTaskFlow.instance), id(SingleTaskFlow.instance))
        self.assertEqual(SingleTaskFlow, type(SingleTaskFlow.instance))
