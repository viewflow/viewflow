from django.conf.urls import include, url
from django.shortcuts import render, redirect
from django_webtest import WebTest

from viewflow import flow
from viewflow.base import Flow, this
from viewflow import views as viewflow

from .. import integration_test
from ... import urls


@flow.flow_start_view()
def start_view(request, activation):
    activation.prepare(user=request.user, data=request.POST or None)

    if request.method == 'POST':
        activation.done()
        return redirect('/')

    return render(request, 'viewflow/flow/start.html', {'activation': activation})


@flow.flow_view()
def task_view(request, activation):
    activation.prepare()
    if request.method == 'POST':
        activation.done()
        return redirect('/')

    return render(request, 'viewflow/flow/start.html', {'activation': activation})


class ViewFlow(Flow):
    start = flow.Start(start_view).Next(this.task)
    task = flow.View(task_view).Next(this.end)
    end = flow.End()


urlpatterns = [
    url(r'^test/', include([
        ViewFlow.instance.urls,
        url('^$', viewflow.ProcessListView.as_view(), name='index'),
        url('^tasks/$', viewflow.TaskListView.as_view(), name='tasks'),
        url('^queue/$', viewflow.QueueListView.as_view(), name='queue'),
        url('^details/(?P<process_pk>\d+)/$', viewflow.ProcessDetailView.as_view(), name='details'),
    ], namespace=ViewFlow.instance.namespace), {'flow_cls': ViewFlow})] + urls.urlpatterns


@integration_test
class TestViewFlow(WebTest):
    urls = __name__

    def setUp(self):
        from django.contrib.auth.models import User
        self.user = User.objects.create_superuser('admin', 'admin@admin.com', 'admin')

    def test_view_flow(self):
        # start
        start_form = self.app.get('/test/start/', user=self.user.username).form
        start_form.submit('_start').follow()

        process = ViewFlow.process_cls.objects.get()
        task = process.get_task(ViewFlow.task)
        task_url = task.get_absolute_url(user=self.user)

        # assign
        self.assertIn('assign', task_url)
        assign_form = self.app.get(task_url, user=self.user.username).form
        assign_form.submit('assign')

        task = process.get_task(ViewFlow.task)
        task_url = task.get_absolute_url(user=self.user)

        # execute
        self.assertNotIn('details', task_url)
        execute_form = self.app.get(task_url, user=self.user.username).form
        execute_form.submit('_done').follow()

        # check
        tasks = process.task_set.all()
        self.assertEqual(3, tasks.count())
        self.assertTrue(all(task.finished is not None for task in tasks))
