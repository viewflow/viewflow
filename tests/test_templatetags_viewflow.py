from django.core.urlresolvers import resolve
from django.conf.urls import include, url
from django.contrib.auth.models import User
from django.http.request import QueryDict
from django.template import Template, Context
from django.test import TestCase, RequestFactory

from viewflow import flow
from viewflow.base import this, Flow
from viewflow.flow import views


class Test(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/test/')
        self.request.user = User(username='test')
        self.request.resolver_match = resolve('/test/')

    def test_flowurl_by_flow_label(self):
        url = Template("{% load viewflow %}{% flowurl 'tests/TestTemplateTagsFlow' 'index' %}").render(
            Context({'request': self.request}))
        self.assertEqual('/test/', url)

    def test_flowurl_by_flow_class(self):
        url = Template("{% load viewflow %}{% flowurl flow_cls 'tasks' %}").render(
            Context({'request': self.request, 'flow_cls': TestTemplateTagsFlow}))
        self.assertEqual('/test/tasks/', url)

    def test_flowurl_by_process(self):
        act = TestTemplateTagsFlow.start.run()
        url = Template("{% load viewflow %}{% flowurl process 'queue' %}").render(
            Context({'request': self.request, 'process': act.process}))
        self.assertEqual('/test/queue/', url)

    def test_flowurl_by_task(self):
        act = TestTemplateTagsFlow.start.run()
        task = act.process.get_task(TestTemplateTagsFlow.view)
        url = Template("{% load viewflow %}{% flowurl task 'assign' user=user %}").render(
            Context({'request': self.request, 'task': task, 'user': User()}))
        self.assertEqual(
            '/test/{}/view/{}/assign/'.format(act.process.pk, task.pk),
            url)

    def test_flowurl_guess_by_task(self):
        act = TestTemplateTagsFlow.start.run()
        task = act.process.get_task(TestTemplateTagsFlow.view)
        url = Template("{% load viewflow %}{% flowurl task user=user %}").render(
            Context({'request': self.request, 'task': task, 'user': User()}))
        self.assertEqual(
            '/test/{}/view/{}/assign/'.format(act.process.pk, task.pk),
            url)

    def test_flow_perms(self):
        act = TestTemplateTagsFlow.start.run()
        task = act.process.get_task(TestTemplateTagsFlow.view)
        user = User.objects.create(username="test")
        perms = Template("{% load viewflow %}{% flow_perms user task as perms %}{{ perms|join:',' }}").render(
            Context({'request': self.request, 'task': task, 'user': user}))
        self.assertEqual('can_execute,can_assign', perms)

    def test_include_process_data(self):
        act = TestTemplateTagsFlow.start.run()
        user = User.objects.create(username="test")
        request = type('Request', (object,), {'user': user, 'GET': QueryDict(query_string=None)})
        process_data = Template("{% load viewflow %}{% include_process_data process %}").render(
            Context({'request': self.request, 'process': act.process, 'request': request}))
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
    view = flow.View(views.FlowView).Next(this.end)
    end = flow.End()


urlpatterns = [
    url(r'^test/', include([
        TestTemplateTagsFlow.instance.urls,
        url('^$', views.ProcessListView.as_view(flow_cls=TestTemplateTagsFlow), name='index'),
        url('^tasks/$', views.TaskListView.as_view(flow_cls=TestTemplateTagsFlow), name='tasks'),
        url('^queue/$', views.QueueListView.as_view(flow_cls=TestTemplateTagsFlow), name='queue'),
        url('^details/(?P<process_pk>\d+)/$',
            views.DetailProcessView.as_view(flow_cls=TestTemplateTagsFlow), name='details'),
        url('^action/cancel/(?P<process_pk>\d+)/$',
            views.CancelProcessView.as_view(flow_cls=TestTemplateTagsFlow), name='action_cancel'),
    ], namespace='testtemplatetags')),
]
