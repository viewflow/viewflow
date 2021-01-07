from django.urls import include, re_path
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.urls import resolve

from viewflow import flow
from viewflow.base import Flow, this
from viewflow.flow import views, viewset
from viewflow.models import Process


class Test(TestCase):
    def test_all_processlist_view(self):
        view = views.AllProcessListView.as_view(ns_map={ListViewTestFlow: 'listviewtest'})

        request = RequestFactory().get('/processes/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request)
        self.assertEqual(response.template_name, ['viewflow/site_index.html', 'viewflow/process_list.html'])

    def test_all_tasklist_view(self):
        view = views.AllTaskListView.as_view(ns_map={ListViewTestFlow: 'listviewtest'})

        request = RequestFactory().get('/tasks/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request)
        self.assertEqual(response.template_name, ['viewflow/site_tasks.html', 'viewflow/task_list.html'])

    def test_all_queuelist_view(self):
        view = views.AllQueueListView.as_view(ns_map={ListViewTestFlow: 'listviewtest'})

        request = RequestFactory().get('/queues/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request)
        self.assertEqual(response.template_name, ['viewflow/site_queue.html', 'viewflow/task_list.html'])

    def test_all_archivelist_view(self):
        view = views.AllArchiveListView.as_view(ns_map={ListViewTestFlow: 'listviewtest'})

        request = RequestFactory().get('/archives/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request)
        self.assertEqual(response.template_name, ['viewflow/site_archive.html', 'viewflow/task_list.html'])

    def test_processlist_view(self):
        view = views.ProcessListView.as_view()

        request = RequestFactory().get('/process_list/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request, flow_class=ListViewTestFlow)
        self.assertEqual(response.template_name,
                         ('tests/test_views_list/listviewtest/process_list.html',
                          'viewflow/flow/process_list.html'))

    def test_processdetail_view(self):
        process = Process.objects.create(flow_class=ListViewTestFlow)
        view = views.DetailProcessView.as_view()

        request = RequestFactory().get('/process/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request, flow_class=ListViewTestFlow, process_pk=process.pk)

        self.assertEqual(response.template_name,
                         ('tests/test_views_list/listviewtest/process_detail.html',
                          'viewflow/flow/process_detail.html'))

    def test_tasklist_view(self):
        view = views.TaskListView.as_view()

        request = RequestFactory().get('/task_list/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request, flow_class=ListViewTestFlow)

        self.assertEqual(response.template_name,
                         ('tests/test_views_list/listviewtest/task_list.html',
                          'viewflow/flow/task_list.html'))

    def test_queuelist_view(self):
        view = views.QueueListView.as_view()

        request = RequestFactory().get('/task_list/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request, flow_class=ListViewTestFlow)

        self.assertEqual(response.template_name,
                         ('tests/test_views_list/listviewtest/queue.html',
                          'viewflow/flow/queue.html'))


class ListViewTestFlow(Flow):
    start1 = flow.StartFunction().Next(this.test_task)
    start2 = flow.Start(lambda request: None).Permission('auth.start_flow_perm').Next(this.test_task)
    start3 = flow.Start(lambda request: None).Next(this.test_task)
    test_task = flow.View(lambda request: None).Next(this.end)
    end = flow.End()


urlpatterns = [
    re_path(r'^test/', include((viewset.FlowViewSet(ListViewTestFlow).urls, 'listviewtest')))
]

try:
    from django.test import override_settings
    Test = override_settings(ROOT_URLCONF=__name__)(Test)
except ImportError:
    """
    django 1.6
    """
    Test.urls = __name__
