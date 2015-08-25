from django.conf.urls import include, url
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.utils import timezone

from viewflow import flow, views
from viewflow.base import Flow, this
from viewflow.models import Task, Process
from viewflow.views import list


class Test(TestCase):
    urls = __name__

    def test_flow_start_actions(self):
        user = User.objects.create(username='superuser', is_superuser=True)
        actions = list.flow_start_actions(ListViewTestFlow, user)

        self.assertEqual(actions, [
            ('/test/start2/', 'start2'),
            ('/test/start3/', 'start3')])

        user = User.objects.create(username='user', is_superuser=False)
        actions = list.flow_start_actions(ListViewTestFlow, user)
        self.assertEqual(actions, [('/test/start3/', 'start3')])

    def test_flows_start_actions(self):
        user = User.objects.create(username='superuser', is_superuser=True)
        actions = list.flows_start_actions([ListViewTestFlow], user)

        self.assertEqual(actions, {
            ListViewTestFlow: [
                ('/test/start2/', 'start2'),
                ('/test/start3/', 'start3')]})

    def test_task_filter(self):
        process = Process.objects.create(flow_cls=ListViewTestFlow)
        task1 = Task.objects.create(process=process, flow_task=ListViewTestFlow.start1)
        task1.created = timezone.now().replace(year=1900)
        task1.save()
        task2 = Task.objects.create(process=process, flow_task=ListViewTestFlow.start2)

        # filter by current year
        with self.assertNumQueries(2):
            task_filter = list.TaskFilter({'created': 4}, Task.objects.all())
            str(task_filter.form)

        self.assertEqual([task for task in task_filter.qs], [task2])

    def test_all_processlist_view(self):
        view = list.AllProcessListView.as_view()

        request = RequestFactory().get('/processes/')
        request.user = User(username='test', is_superuser=True)

        response = view(request, flow_classes=[ListViewTestFlow])
        self.assertEqual(response.template_name, 'viewflow/site_index.html')

    def test_all_tasklist_view(self):
        view = list.AllTaskListView.as_view()

        request = RequestFactory().get('/tasks/')
        request.user = User(username='test', is_superuser=True)

        response = view(request, flow_classes=[ListViewTestFlow])
        self.assertEqual(response.template_name, 'viewflow/site_tasks.html')

    def test_all_queuelist_view(self):
        view = list.AllQueueListView.as_view()

        request = RequestFactory().get('/queues/')
        request.user = User(username='test', is_superuser=True)

        response = view(request, flow_classes=[ListViewTestFlow])
        self.assertEqual(response.template_name, 'viewflow/site_queue.html')

    def test_all_archivelist_view(self):
        view = list.AllArchiveListView.as_view()

        request = RequestFactory().get('/archives/')
        request.user = User(username='test', is_superuser=True)

        response = view(request, flow_classes=[ListViewTestFlow])
        self.assertEqual(response.template_name, 'viewflow/site_archive.html')

    def test_processlist_view(self):
        view = list.ProcessListView.as_view()

        request = RequestFactory().get('/process_list/')
        request.user = User(username='test', is_superuser=True)

        response = view(request, flow_cls=ListViewTestFlow)
        self.assertEqual(response.template_name,
                         ('tests/test_views_list/listviewtest/process_list.html',
                          'viewflow/flow/process_list.html'))

    def test_processdetail_view(self):
        process = Process.objects.create(flow_cls=ListViewTestFlow)
        view = list.ProcessDetailView.as_view()

        request = RequestFactory().get('/process/')
        request.user = User(username='test', is_superuser=True)

        response = view(request, flow_cls=ListViewTestFlow, process_pk=process.pk)

        self.assertEqual(response.template_name,
                         ('tests/test_views_list/listviewtest/process_details.html',
                          'viewflow/flow/process_details.html'))

    def test_tasklist_view(self):
        view = list.TaskListView.as_view()

        request = RequestFactory().get('/task_list/')
        request.user = User(username='test', is_superuser=True)

        response = view(request, flow_cls=ListViewTestFlow)

        self.assertEqual(response.template_name,
                         ('tests/test_views_list/listviewtest/task_list.html',
                          'viewflow/flow/task_list.html'))

    def test_queuelist_view(self):
        view = list.QueueListView.as_view()

        request = RequestFactory().get('/task_list/')
        request.user = User(username='test', is_superuser=True)

        response = view(request, flow_cls=ListViewTestFlow)

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
    url(r'^test/', include([
        ListViewTestFlow.instance.urls,
        url('^$', views.ProcessListView.as_view(), name='index'),
        url('^tasks/$', views.TaskListView.as_view(), name='tasks'),
        url('^queue/$', views.QueueListView.as_view(), name='queue'),
        url('^details/(?P<process_pk>\d+)/$', views.ProcessDetailView.as_view(), name='details'),
    ], namespace=ListViewTestFlow.instance.namespace), {'flow_cls': ListViewTestFlow})
]
