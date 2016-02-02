from django.conf.urls import include, url
from django.contrib.auth.models import User
from django.template import Template, Context
from django.test import TestCase

from viewflow import flow
from viewflow import views as viewflow
from viewflow.base import this, Flow


class Test(TestCase):
    def test_flowurl_by_flow_label(self):
        url = Template("{% load viewflow %}{% flowurl 'tests/TestTemplateTagsFlow' 'index' %}").render(Context())
        self.assertEqual('/test_tempaltetags/', url)

    def test_flowurl_by_flow_class(self):
        url = Template("{% load viewflow %}{% flowurl flow_cls 'tasks' %}").render(
            Context({'flow_cls': TestTemplateTagsFlow}))
        self.assertEqual('/test_tempaltetags/tasks/', url)

    def test_flowurl_by_process(self):
        act = TestTemplateTagsFlow.start.run()
        url = Template("{% load viewflow %}{% flowurl process 'queue' %}").render(
            Context({'process': act.process}))
        self.assertEqual('/test_tempaltetags/queue/', url)

    def test_flowurl_by_task(self):
        act = TestTemplateTagsFlow.start.run()
        task = act.process.get_task(TestTemplateTagsFlow.view)
        url = Template("{% load viewflow %}{% flowurl task 'assign' user=user %}").render(
            Context({'task': task, 'user': User()}))
        self.assertEqual(
            '/test_tempaltetags/{}/view/{}/assign/'.format(act.process.pk, task.pk),
            url)

    def test_flowurl_guess_by_task(self):
        act = TestTemplateTagsFlow.start.run()
        task = act.process.get_task(TestTemplateTagsFlow.view)
        url = Template("{% load viewflow %}{% flowurl task user=user %}").render(
            Context({'task': task, 'user': User()}))
        self.assertEqual(
            '/test_tempaltetags/{}/view/{}/assign/'.format(act.process.pk, task.pk),
            url)

    def test_flow_perms(self):
        act = TestTemplateTagsFlow.start.run()
        task = act.process.get_task(TestTemplateTagsFlow.view)
        user = User.objects.create(username="test")
        perms = Template("{% load viewflow %}{% flow_perms user task as perms %}{{ perms|join:',' }}").render(
            Context({'task': task, 'user': user}))
        self.assertEqual('can_execute,can_assign', perms)

    def test_include_process_data(self):
        act = TestTemplateTagsFlow.start.run()
        user = User.objects.create(username="test")
        request = type('Request', (object,), {'user': user})
        process_data = Template("{% load viewflow %}{% include_process_data process %}").render(
            Context({'process': act.process, 'request': request}))
        self.assertIn('Test Template Tags', process_data)


try:
    from django.test import override_settings
    Test = override_settings(ROOT_URLCONF=__name__)(Test)
except ImportError:
    """
    django 1.6
    """
    Test.urls = __name__


class TestTemplateTagsFlow(Flow):
    start = flow.StartFunction().Next(this.view)
    view = flow.View(viewflow.ProcessView).Next(this.end)
    end = flow.End()


urlpatterns = [
    url(r'^test_tempaltetags/', include([
        TestTemplateTagsFlow.instance.urls,
        url('^$', viewflow.ProcessListView.as_view(), name='index'),
        url('^tasks/$', viewflow.TaskListView.as_view(), name='tasks'),
        url('^queue/$', viewflow.QueueListView.as_view(), name='queue'),
        url('^details/(?P<process_pk>\d+)/$', viewflow.ProcessDetailView.as_view(), name='details'),
        url('^action/cancel/(?P<process_pk>\d+)/$', viewflow.ProcessCancelView.as_view(), name='action_cancel'),
    ], namespace=TestTemplateTagsFlow.instance.namespace), {'flow_cls': TestTemplateTagsFlow}),
]
