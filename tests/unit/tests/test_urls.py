from django.test import TestCase
from unit.flows import SingleTaskFlow


class TestURLPatterns(TestCase):
    def test_patterns_contains_all_flow(self):
        patterns = SingleTaskFlow.instance.urls

        self.assertIsNotNone(patterns)
        self.assertEqual(3, len(patterns))

        urls, app, namespace = patterns
        self.assertEqual(4, len(urls))
        self.assertEqual('viewflow', app)
        self.assertEqual(SingleTaskFlow._meta.namespace, namespace)


# Test reverse url

# Test flowurl tag

# Test task.get_absolute_url
