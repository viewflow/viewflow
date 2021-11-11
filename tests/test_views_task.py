from django.urls import resolve, include, re_path
from django.db import models
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.views import generic

from viewflow import flow
from viewflow.activation import STATUS
from viewflow.base import Flow, this
from viewflow.flow import views, viewset


class Test(TestCase):
    def test_taskview_mixin_with_create_view(self):
        class FlowView(views.FlowViewMixin, generic.CreateView):
            model = TaskViewFlowEntity
            fields = []

        act = TaskViewTestFlow.start.run()
        task = act.process.get_task(TaskViewTestFlow.task)
        view = FlowView.as_view()
        user = User.objects.create(username='test', is_superuser=True)

        # unassigned redirect
        request = RequestFactory().get('/start/')
        request.user = user
        request.resolver_match = resolve('/test/1/task/1/')
        response = view(request, flow_class=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/test/{}/task/{}/detail/'.format(act.process.pk, task.pk))

        # assigned get
        act = task.activate()
        act.assign(user=user)

        request = RequestFactory().get('/start/')
        request.user = user
        request.resolver_match = resolve('/test/1/task/1/')
        response = view(request, flow_class=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name,
                         ('tests/test_views_task/taskviewtest/task.html',
                          'tests/test_views_task/taskviewtest/task.html',
                          'viewflow/flow/task.html'))
        # assigned post
        request = RequestFactory().post('/task/')
        request.user = user
        request.resolver_match = resolve('/test/1/task/1/')
        response = view(request, flow_class=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 302)

        task.refresh_from_db()
        self.assertEqual(task.status, STATUS.DONE)

    def test_flowview(self):
        view = views.UpdateProcessView.as_view()
        user = User.objects.create(username='test', is_superuser=True)

        act = TaskViewTestFlow.start.run()
        task = act.process.get_task(TaskViewTestFlow.task)

        # assigned get
        act = task.activate()
        act.assign(user=user)

        request = RequestFactory().get('/start/')
        request.user = user
        request.resolver_match = resolve('/test/1/task/1/')
        response = view(request, flow_class=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name,
                         ('tests/test_views_task/taskviewtest/task.html',
                          'tests/test_views_task/taskviewtest/task.html',
                          'viewflow/flow/task.html'))
        # assigned post
        request = RequestFactory().post('/task/')
        request.user = user
        request.resolver_match = resolve('/test/1/task/1/')
        response = view(request, flow_class=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 302)

        task.refresh_from_db()
        self.assertEqual(task.status, STATUS.DONE)

    def test_assignview(self):
        view = views.AssignTaskView.as_view()
        user = User.objects.create(username='test', is_superuser=True)

        act = TaskViewTestFlow.start.run()
        task = act.process.get_task(TaskViewTestFlow.task)

        # unassigned get
        request = RequestFactory().get('/start/')
        request.user = user
        request.resolver_match = resolve('/test/1/task/1/')

        response = view(request, flow_class=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name,
                         ('tests/test_views_task/taskviewtest/task_assign.html',
                          'tests/test_views_task/taskviewtest/task_assign.html',
                          'viewflow/flow/task_assign.html'))

        # unassigned post
        request = RequestFactory().post('/task/')
        request.user = user
        request.resolver_match = resolve('/test/1/task/1/')
        response = view(request, flow_class=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/test/{}/task/{}/'.format(act.process.pk, task.pk))

        task.refresh_from_db()
        self.assertEqual(task.status, STATUS.ASSIGNED)
        self.assertEqual(task.owner, user)

        # assigned get
        request = RequestFactory().get('/start/')
        request.user = user
        request.resolver_match = resolve('/test/1/task/1/')

        response = view(request, flow_class=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 302)


class TaskViewTestFlow(Flow):
    start = flow.StartFunction().Next(this.task)
    task = flow.View(lambda request: None).Next(this.end)
    end = flow.End()


class TaskViewFlowEntity(models.Model):
    pass


urlpatterns = [
    re_path(r'^test/', include((viewset.FlowViewSet(TaskViewTestFlow).urls, 'taskviewtest')))
]

try:
    from django.test import override_settings
    Test = override_settings(ROOT_URLCONF=__name__)(Test)
except ImportError:
    """
    django 1.6
    """
    Test.urls = __name__
