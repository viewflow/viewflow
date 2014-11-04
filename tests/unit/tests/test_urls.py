from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.test import TestCase

from viewflow.models import Process, Task
from ..flows import SingleTaskFlow, AllTaskFlow

urlpatterns = patterns('',  # NOQA
    url(r'^single_flow/', include(SingleTaskFlow.instance.urls)),
    url(r'^alltask_flow/', include(AllTaskFlow.instance.urls)))


class TestURLPatterns(TestCase):
    def test_tterns_contains_all_flow(self):
        patterns = SingleTaskFlow.instance.urls

        self.assertIsNotNone(patterns)
        self.assertEqual(3, len(patterns))

        urls, app, namespace = patterns

        self.assertEqual(7, len(urls))
        self.assertEqual('viewflow', app)
        self.assertEqual(SingleTaskFlow._meta.namespace, namespace)


class TestURLReverse(TestCase):
    urls = 'tests.unit.tests.test_urls'

    def test_django_reverse_flow_urls_succeed(self):
        reverse('viewflow:start', current_app=SingleTaskFlow._meta.namespace)
        reverse('viewflow:task', args=[1, 1], current_app=SingleTaskFlow._meta.namespace)
        reverse('viewflow:task__assign', args=[1, 1], current_app=SingleTaskFlow._meta.namespace)

    def test_flow_reverse_urls_succeed(self):
        process = Process.objects.create(flow_cls=SingleTaskFlow)

        task = Task.objects.create(process=process, flow_task=SingleTaskFlow.start)
        SingleTaskFlow.instance.get_user_task_url(task=task, user=None)

        task = Task.objects.create(process=process, flow_task=SingleTaskFlow.task)
        SingleTaskFlow.instance.get_user_task_url(task=task, user=None)

        task = Task.objects.create(process=process, flow_task=SingleTaskFlow.end)
        SingleTaskFlow.instance.get_user_task_url(task=task, user=None)

    def test_get_task_absolute_url_succeed(self):
        process = Process.objects.create(flow_cls=SingleTaskFlow)
        task = Task.objects.create(process=process, flow_task=SingleTaskFlow.task)
        task.get_absolute_url()


class TestFlowUrlTag(TestCase):
    urls = 'tests.unit.tests.test_urls'

    def setUp(self):
        self.process = Process.objects.create(flow_cls=SingleTaskFlow)
        self.task = Task.objects.create(process=self.process, flow_task=SingleTaskFlow.task)

    def _test_task_resolve_succeed(self):
        template = Template(
            "{% load viewflow %}{% flowurl task %}")

        self.assertEqual(template.render(Context({'task': self.task})),
                         '/single_flow/{}/task/{}/'.format(self.task.process_id, self.task.pk))

    def _test_task_assign_resolve_succeed(self):
        template = Template(
            "{% load viewflow %}{% flowurl task 'assign' %}")

        self.assertEqual(template.render(Context({'task': self.task})),
                         '/single_flow/{}/task/{}/assign/'.format(self.task.process_id, self.task.pk))
