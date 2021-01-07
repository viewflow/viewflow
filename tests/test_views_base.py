from django.urls import include, re_path
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.urls import resolve


from viewflow import flow
from viewflow.base import Flow, this
from viewflow.flow import views, viewset


class Test(TestCase):
    def test_get_next_task_url_flow_index(self):
        request = RequestFactory().get('/test/')
        request.user = User(username='test')
        request.resolver_match = resolve('/test/')

        next_url = views.get_next_task_url(request, BaseViewTestFlow.process_class(flow_class=BaseViewTestFlow))
        self.assertEqual(next_url, '/test/')

    def test_get_next_task_url_process_list(self):
        process = BaseViewTestFlow.process_class.objects.create(flow_class=BaseViewTestFlow)
        request = RequestFactory().get('/test/')
        request.user = User(username='test')
        request.resolver_match = resolve('/test/')

        next_url = views.get_next_task_url(request, process)
        self.assertEqual(next_url, '/test/{}/'.format(process.pk))

    def test_get_next_task_url_back(self):
        request = RequestFactory().get('/test/', {'back': '/test_back_url/'})
        request.user = User(username='test')
        request.resolver_match = resolve('/test/')

        next_url = views.get_next_task_url(request, None)
        self.assertEqual(next_url, '/test_back_url/')

        request = RequestFactory().get('/test/', {'back': 'http://unsafe.com/test_back_url/'})
        request.user = User(username='test')
        request.resolver_match = resolve('/test/')

        next_url = views.get_next_task_url(request, None)
        self.assertEqual(next_url, '/')

    def test_get_next_task_url_continue_assigned_task(self):
        user = User.objects.create(username='test')
        act = BaseViewTestFlow.start.run()
        task = act.process.get_task(BaseViewTestFlow.test_task)
        task.activate().assign(user)

        request = RequestFactory().post('/done/', {'_continue': '1'})
        request.user = user
        request.resolver_match = resolve('/test/')

        next_url = views.get_next_task_url(request, act.process)
        self.assertEqual(next_url, '/test/{}/test_task/{}/'.format(task.process_id, task.pk))

    def test_get_next_task_url_continue_unassigned_task(self):
        user = User.objects.create(username='test')

        act = BaseViewTestFlow.start.run()
        task = act.process.get_task(BaseViewTestFlow.test_task)

        request = RequestFactory().post('/done/', {'_continue': '1'})
        request.user = user
        request.resolver_match = resolve('/test/')

        next_url = views.get_next_task_url(request, act.process)
        self.assertEqual(next_url, '/test/{}/test_task/{}/assign/'.format(task.process_id, task.pk))

    def test_detail_view(self):
        act = BaseViewTestFlow.start.run()
        view = views.DetailTaskView.as_view()
        task = act.process.get_task(BaseViewTestFlow.test_task)

        # get
        request = RequestFactory().get('/detail/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')
        response = view(
            request, flow_class=BaseViewTestFlow, flow_task=BaseViewTestFlow.test_task,
            process_pk=act.process.pk, task_pk=task.pk)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.template_name,
                         ('tests/test_views_base/baseviewtest/test_task_detail.html',
                          'tests/test_views_base/baseviewtest/task_detail.html',
                          'viewflow/flow/task_detail.html'))
        self.assertEqual(response.context_data['activation'].process, act.process)


class BaseViewTestFlow(Flow):
    start = flow.StartFunction().Next(this.test_task)
    test_task = flow.View(lambda request: None).Next(this.end)
    end = flow.End()


urlpatterns = [
    re_path(r'^test/', include((viewset.FlowViewSet(BaseViewTestFlow).urls, 'baseviewtest')))
]

try:
    from django.test import override_settings
    Test = override_settings(ROOT_URLCONF=__name__)(Test)
except ImportError:
    """
    django 1.6
    """
    Test.urls = __name__
