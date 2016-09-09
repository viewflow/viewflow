from django.core.urlresolvers import resolve
from django.conf.urls import include, url
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.utils import timezone

from viewflow import flow
from viewflow.base import Flow, this
from viewflow.models import Task, Process
from viewflow.flow import views, routers
from viewflow.flow.views.list import TaskFilter


class Test(TestCase):
    def test_task_filter(self):
        process = Process.objects.create(flow_class=ListViewTestFlow)
        task1 = Task.objects.create(process=process, flow_task=ListViewTestFlow.start1)
        task1.created = timezone.now().replace(year=1900)
        task1.save()
        task2 = Task.objects.create(process=process, flow_task=ListViewTestFlow.start2)

        # filter by current year
        with self.assertNumQueries(2):
            task_filter = TaskFilter({'created': 4}, Task.objects.all())
            str(task_filter.form)

        self.assertEqual([task for task in task_filter.qs], [task2])

    def test_all_processlist_view(self):
        view = views.AllProcessListView.as_view(ns_map={'listviewtest': ListViewTestFlow})

        request = RequestFactory().get('/processes/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request)
        self.assertEqual(response.template_name, 'viewflow/site_index.html')

    def test_all_tasklist_view(self):
        view = views.AllTaskListView.as_view(ns_map={'listviewtest': ListViewTestFlow})

        request = RequestFactory().get('/tasks/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request)
        self.assertEqual(response.template_name, 'viewflow/site_tasks.html')

    def test_all_queuelist_view(self):
        view = views.AllQueueListView.as_view(ns_map={'listviewtest': ListViewTestFlow})

        request = RequestFactory().get('/queues/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request)
        self.assertEqual(response.template_name, 'viewflow/site_queue.html')

    def test_all_archivelist_view(self):
        view = views.AllArchiveListView.as_view(ns_map={'listviewtest': ListViewTestFlow})

        request = RequestFactory().get('/archives/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request)
        self.assertEqual(response.template_name, 'viewflow/site_archive.html')

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
    url(r'^test/', include(routers.FlowRouter(ListViewTestFlow).urls, namespace='listviewtest'))
]

try:
    from django.test import override_settings
    Test = override_settings(ROOT_URLCONF=__name__)(Test)
except ImportError:
    """
    django 1.6
    """
    Test.urls = __name__
