from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse
from django.test import TestCase
from viewflow.models import Process, Task
from unit.flows import SingleTaskFlow

urlpatterns = patterns('',  # NOQA
    url(r'^flow/', include(SingleTaskFlow.instance.urls)))


class TestURLPatterns(TestCase):
    def test_patterns_contains_all_flow(self):
        patterns = SingleTaskFlow.instance.urls

        self.assertIsNotNone(patterns)
        self.assertEqual(3, len(patterns))

        urls, app, namespace = patterns
        self.assertEqual(3, len(urls))
        self.assertEqual('viewflow', app)
        self.assertEqual(SingleTaskFlow._meta.namespace, namespace)


class TestURLReverse(TestCase):
    urls = 'unit.tests.test_urls'

    def test_django_reverse_flow_urls_succeed(self):
        reverse('viewflow:index', current_app=SingleTaskFlow._meta.app_label)
        reverse('viewflow:start', current_app=SingleTaskFlow._meta.app_label)
        reverse('viewflow:task', args=[1], current_app=SingleTaskFlow._meta.app_label)

    def test_flow_reverse_urls_succeed(self):
        SingleTaskFlow.instance.reverse(
            Task(process=Process(flow_cls=SingleTaskFlow),
                 flow_task=SingleTaskFlow.start))
        SingleTaskFlow.instance.reverse(
            Task(process=Process(flow_cls=SingleTaskFlow),
                 flow_task=SingleTaskFlow.task,
                 pk=1))
        SingleTaskFlow.instance.reverse(
            Task(process=Process(flow_cls=SingleTaskFlow),
                 flow_task=SingleTaskFlow.end,
                 pk=1))

    def test_get_task_absolute_url_succeed(self):
        task = Task(process=Process(flow_cls=SingleTaskFlow),
                    flow_task=SingleTaskFlow.task,
                    pk=1)
        task.get_absolute_url()

# Test flowurl tag
