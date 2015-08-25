from django.conf.urls import include, url
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory


from viewflow import flow, views
from viewflow.base import Flow, this
from viewflow.views import base


class Test(TestCase):
    urls = __name__

    def test_get_next_task_url_flow_index(self):
        request = RequestFactory().get('/test/')
        request.user = User(username='test')

        next_url = base.get_next_task_url(request, BaseViewTestFlow.process_cls(flow_cls=BaseViewTestFlow))
        self.assertEqual(next_url, '/test/')

    def test_get_next_task_url_process_list(self):
        process = BaseViewTestFlow.process_cls.objects.create(flow_cls=BaseViewTestFlow)
        request = RequestFactory().get('/test/')
        request.user = User(username='test')

        next_url = base.get_next_task_url(request, process)
        self.assertEqual(next_url, '/test/details/{}/'.format(process.pk))
            
    def test_get_next_task_url_back(self):
        request = RequestFactory().get('/test/', {'back': '/test_back_url/'})
        request.user = User(username='test')

        next_url = base.get_next_task_url(request, None)
        self.assertEqual(next_url, '/test_back_url/')

        request = RequestFactory().get('/test/', {'back': 'http://unsafe.com/test_back_url/'})
        request.user = User(username='test')

        next_url = base.get_next_task_url(request, None)
        self.assertEqual(next_url, '/')

    def test_get_next_task_url_continue_assigned_task(self):
        user = User.objects.create(username='test')
        act = BaseViewTestFlow.start.run()
        task = act.process.get_task(BaseViewTestFlow.test_task)
        task.activate().assign(user)

        request = RequestFactory().post('/done/', {'_continue': '1'})
        request.user = user

        next_url = base.get_next_task_url(request, act.process)
        self.assertEqual(next_url, '/test/{}/test_task/{}/'.format(task.process_id, task.pk))

    def test_get_next_task_url_continue_unassigned_task(self):
        user = User.objects.create(username='test')

        act = BaseViewTestFlow.start.run()
        task = act.process.get_task(BaseViewTestFlow.test_task)

        request = RequestFactory().post('/done/', {'_continue': '1'})
        request.user = user

        next_url = base.get_next_task_url(request, act.process)
        self.assertEqual(next_url, '/test/{}/test_task/{}/assign/'.format(task.process_id, task.pk))

    def test_details_view(self):
        act = BaseViewTestFlow.start.run()
        view = base.DetailsView.as_view()
        task = act.process.get_task(BaseViewTestFlow.test_task)

        # get
        request = RequestFactory().get('/details/')
        request.user = User(username='test', is_superuser=True)
        response = view(
            request, flow_cls=BaseViewTestFlow, flow_task=BaseViewTestFlow.test_task,
            process_pk=act.process.pk, task_pk=task.pk)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.template_name,
                         ('tests/test_views_base/baseviewtest/test_task_details.html',
                          'tests/test_views_base/baseviewtest/task_details.html',
                          'viewflow/flow/task_details.html'))
        self.assertEqual(response.context_data['activation'].process, act.process)


class BaseViewTestFlow(Flow):
    start = flow.StartFunction().Next(this.test_task)
    test_task = flow.View(lambda request: None).Next(this.end)
    end = flow.End()


urlpatterns = [
    url(r'^test/', include([
        BaseViewTestFlow.instance.urls,
        url('^$', views.ProcessListView.as_view(), name='index'),
        url('^tasks/$', views.TaskListView.as_view(), name='tasks'),
        url('^queue/$', views.QueueListView.as_view(), name='queue'),
        url('^details/(?P<process_pk>\d+)/$', views.ProcessDetailView.as_view(), name='details'),
    ], namespace=BaseViewTestFlow.instance.namespace), {'flow_cls': BaseViewTestFlow})
]
