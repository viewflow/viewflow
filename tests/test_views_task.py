from django.conf.urls import include, url
from django.db import models
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.views import generic

from viewflow import flow, views
from viewflow.activation import STATUS
from viewflow.base import Flow, this
from viewflow.views import task as task_views


class Test(TestCase):
    urls = __name__

    def test_taskview_mixin_with_create_view(self):
        class StartView(task_views.TaskViewMixin, generic.CreateView):
            model = TaskViewFlowEntity
            fields = []

        act = TaskViewTestFlow.start.run()
        task = act.process.get_task(TaskViewTestFlow.task)
        view = StartView.as_view()
        user = User.objects.create(username='test', is_superuser=True)

        # unassigned redirect
        request = RequestFactory().get('/start/')
        request.user = user
        response = view(request, flow_cls=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/test/{}/task/{}/details/'.format(act.process.pk, task.pk))

        # assigned get
        act = task.activate()
        act.assign(user=user)

        request = RequestFactory().get('/start/')
        request.user = user
        response = view(request, flow_cls=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name,
                         ('tests/test_views_task/taskviewtest/task.html',
                          'tests/test_views_task/taskviewtest/task.html',
                          'viewflow/flow/task.html'))
        # assigned post
        request = RequestFactory().post('/task/')
        request.user = user
        response = view(request, flow_cls=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 302)

        task.refresh_from_db()
        self.assertEqual(task.status, STATUS.DONE)

    def test_taskactivationview_mixin_with_create_view(self):
        class TaskView(flow.ManagedViewActivation, task_views.TaskActivationViewMixin, generic.CreateView):
            model = TaskViewFlowEntity
            fields = []

        act = TaskViewTestFlow.start.run()
        task = act.process.get_task(TaskViewTestFlow.task)
        view = TaskView.as_view()
        user = User.objects.create(username='test', is_superuser=True)

        # unassigned redirect
        request = RequestFactory().get('/start/')
        request.user = user

        response = view(request, flow_cls=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/test/{}/task/{}/details/'.format(act.process.pk, task.pk))

        # assigned get
        act = task.activate()
        act.assign(user=user)

        request = RequestFactory().get('/start/')
        request.user = user
        response = view(request, flow_cls=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name,
                         ('tests/test_views_task/taskviewtest/task.html',
                          'tests/test_views_task/taskviewtest/task.html',
                          'viewflow/flow/task.html'))
        # assigned post
        request = RequestFactory().post('/task/')
        request.user = user
        response = view(request, flow_cls=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 302)

        task.refresh_from_db()
        self.assertEqual(task.status, STATUS.DONE)

    def test_processview(self):
        view = task_views.ProcessView.as_view()
        user = User.objects.create(username='test', is_superuser=True)

        act = TaskViewTestFlow.start.run()
        task = act.process.get_task(TaskViewTestFlow.task)

        # assigned get
        act = task.activate()
        act.assign(user=user)

        request = RequestFactory().get('/start/')
        request.user = user
        response = view(request, flow_cls=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name,
                         ('tests/test_views_task/taskviewtest/task.html',
                          'tests/test_views_task/taskviewtest/task.html',
                          'viewflow/flow/task.html'))
        # assigned post
        request = RequestFactory().post('/task/')
        request.user = user
        response = view(request, flow_cls=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 302)

        task.refresh_from_db()
        self.assertEqual(task.status, STATUS.DONE)

    def test_assignview(self):
        view = task_views.AssignView.as_view()
        user = User.objects.create(username='test', is_superuser=True)

        act = TaskViewTestFlow.start.run()
        task = act.process.get_task(TaskViewTestFlow.task)

        # unassigned get
        request = RequestFactory().get('/start/')
        request.user = user

        response = view(request, flow_cls=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name,
                         ('tests/test_views_task/taskviewtest/task_assign.html',
                          'tests/test_views_task/taskviewtest/task_assign.html',
                          'viewflow/flow/task_assign.html'))

        # unassigned post
        request = RequestFactory().post('/task/')
        request.user = user
        response = view(request, flow_cls=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/test/{}/task/{}/'.format(act.process.pk, task.pk))

        task.refresh_from_db()
        self.assertEqual(task.status, STATUS.ASSIGNED)
        self.assertEqual(task.owner, user)

        # assigned get
        request = RequestFactory().get('/start/')
        request.user = user

        response = view(request, flow_cls=TaskViewTestFlow, flow_task=TaskViewTestFlow.task,
                        process_pk=act.process.pk, task_pk=task.pk)
        self.assertEqual(response.status_code, 302)


class TaskViewTestFlow(Flow):
    start = flow.StartFunction().Next(this.task)
    task = flow.View(lambda request: None).Next(this.end)
    end = flow.End()


class TaskViewFlowEntity(models.Model):
    pass


urlpatterns = [
    url(r'^test/', include([
        TaskViewTestFlow.instance.urls,
        url('^$', views.ProcessListView.as_view(), name='index'),
        url('^tasks/$', views.TaskListView.as_view(), name='tasks'),
        url('^queue/$', views.QueueListView.as_view(), name='queue'),
        url('^details/(?P<process_pk>\d+)/$', views.ProcessDetailView.as_view(), name='details'),
    ], namespace=TaskViewTestFlow.instance.namespace), {'flow_cls': TaskViewTestFlow})
]
