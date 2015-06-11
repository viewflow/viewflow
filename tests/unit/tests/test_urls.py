from django.conf.urls import include, url
from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.test import TestCase

from viewflow.models import Process, Task
from ..flows import SingleTaskFlow, AllTaskFlow

urlpatterns = [
    url(r'^single_flow/', include([SingleTaskFlow.instance.urls], namespace=SingleTaskFlow.instance.namespace)),
    url(r'^alltask_flow/', include([AllTaskFlow.instance.urls], namespace=AllTaskFlow.instance.namespace))
]


class TestURLPatterns(TestCase):
    def test_patterns_contains_all_flow(self):
        patterns = SingleTaskFlow.instance.urls

        self.assertIsNotNone(patterns)

        self.assertEqual(15, len(patterns.url_patterns))


class TestURLReverse(TestCase):
    urls = 'tests.unit.tests.test_urls'

    def test_django_reverse_flow_urls_succeed(self):
        reverse('{}:start'.format(SingleTaskFlow.instance.namespace))
        reverse('{}:task'.format(SingleTaskFlow.instance.namespace), args=[1, 1])
        reverse('{}:task__assign'.format(SingleTaskFlow.instance.namespace), args=[1, 1])

    def test_flow_reverse_urls_succeed(self):
        process = Process.objects.create(flow_cls=SingleTaskFlow)

        task = Task.objects.create(process=process, flow_task=SingleTaskFlow.start)
        self.assertIsNotNone(task.flow_task.get_task_url(task, url_type='details'))

        task = Task.objects.create(process=process, flow_task=SingleTaskFlow.task)
        self.assertIsNotNone(task.flow_task.get_task_url(task, url_type='details'))

        task = Task.objects.create(process=process, flow_task=SingleTaskFlow.end)
        self.assertIsNotNone(task.flow_task.get_task_url(task, url_type='details'))


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
