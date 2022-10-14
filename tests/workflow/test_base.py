from django.test import TestCase, override_settings
from django.urls import path, resolve

from viewflow import this
from viewflow.workflow import flow


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):  # noqa: D101
    def test_default_process_title_initialized(self):
        self.assertEqual(TestFlow.process_title, 'Test')
        self.assertEqual(TestFlow.instance.app_label, 'tests')
        self.assertEqual(TestFlow.app_name, 'test')
        self.assertEqual(TestFlow.instance.flow_label, 'workflow/test_base/test')
        self.assertIsNone(TestFlow.instance.namespace)

    def test_node_name_initialized(self):
        self.assertEqual('start', TestFlow.start.name)

    def test_node_context_injected(self):
        match = resolve('/1/start/1/detail/')
        self.assertTrue(hasattr(match.url_name, 'extra'))
        self.assertEqual(match.url_name.extra, {
            'flow': TestFlow.instance,
            'node': TestFlow.start,
        })

    def test_node_links_initialized(self):
        self.assertEqual(list(TestFlow.start._incoming()), [])

        start_outgoing = list(TestFlow.start._outgoing())
        end_incoming = list(TestFlow.end._incoming())

        self.assertEqual(len(start_outgoing), 1)
        self.assertEqual(len(end_incoming), 1)

        self.assertEqual(start_outgoing, end_incoming)

    def test_flow_labels(self):
        self.assertEqual(TestFlow.instance.app_name, 'test')
        self.assertEqual(TestFlow.instance.app_label, 'tests')
        self.assertEqual(TestFlow.instance.flow_label, 'workflow/test_base/test')

    def test_flow_nodes_enumeration(self):
        nodes = TestFlow.instance.nodes()
        self.assertEqual(set(nodes), {TestFlow.start, TestFlow.end})
        self.assertEqual(TestFlow.instance.node('start'), TestFlow.start)
        self.assertEqual(TestFlow.instance.node('end'), TestFlow.end)

    def _test_obsolete_missing_node(self):
        """TODO: test_obsolete_missing_node """


class TestFlow(flow.Flow):  # noqa: D101
    start = flow.StartHandle().Next(this.end)
    end = flow.End()


urlpatterns = [
    path('', TestFlow.instance.urls),
]
