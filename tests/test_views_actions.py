from django.conf.urls import include, url
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.utils import timezone

from viewflow import flow
from viewflow.base import Flow, this
from viewflow.activation import STATUS
from viewflow.models import Task
from viewflow.flow.views import actions, process, ProcessView, UnassignView
from viewflow.flow.views import list as list_views


class Test(TestCase):
    def test_process_cancel_view(self):
        act = ActionsTestFlow.start.run()
        view = process.CancelView.as_view()

        # get
        request = RequestFactory().get('/cancel/')
        request.user = User(username='test', is_superuser=True)
        response = view(request, flow_cls=ActionsTestFlow, process_pk=act.process.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name,
                         ('tests/test_views_actions/actionstest/process_cancel.html',
                          'viewflow/flow/process_cancel.html'))
        self.assertEqual(response.context_data['process'], act.process)

        self.assertEqual(len(response.context_data['active_tasks']), 1)
        self.assertEqual(response.context_data['uncancelable_tasks'], [])

        # post
        request = RequestFactory().post('/cancel/', {'_cancel_process': 1})
        request.user = User(username='test', is_superuser=True)
        response = view(request, flow_cls=ActionsTestFlow, process_pk=act.process.pk)
        act.process.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(act.process.status, STATUS.CANCELED)
        canceled_task = act.process.get_task(ActionsTestFlow.task, status=[STATUS.CANCELED])
        self.assertIsNotNone(canceled_task.finished)

    def test_task_undo_view(self):
        act = ActionsTestFlow.start.run()
        view = actions.UndoView.as_view()

        # prepare the process with cancelable start action
        task = act.process.get_task(ActionsTestFlow.task, status=[STATUS.NEW])
        act = task.activate()
        act.cancel()

        start = act.process.get_task(ActionsTestFlow.start, status=[STATUS.DONE])

        # get
        request = RequestFactory().get('/undo/')
        request.user = User(username='test', is_superuser=True)
        response = view(
            request, flow_cls=ActionsTestFlow, flow_task=ActionsTestFlow.start,
            process_pk=act.process.pk, task_pk=start.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name,
                         ('tests/test_views_actions/actionstest/start_undo.html',
                          'tests/test_views_actions/actionstest/task_undo.html',
                          'viewflow/flow/task_undo.html',
                          'viewflow/flow/task_action.html'))
        self.assertEqual(response.context_data['activation'].process, act.process)

        # post
        request = RequestFactory().post('/undo/', {'run_action': 1})
        request.user = User(username='test', is_superuser=True)
        response = view(
            request, flow_cls=ActionsTestFlow, flow_task=ActionsTestFlow.start,
            process_pk=act.process.pk, task_pk=start.pk)
        start.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(start.status, STATUS.CANCELED)
        self.assertEqual(start.process.status, STATUS.CANCELED)
        self.assertIsNotNone(start.finished)

    def test_task_cancel_view(self):
        act = ActionsTestFlow.start.run()
        view = actions.CancelView.as_view()
        task = act.process.get_task(ActionsTestFlow.task, status=[STATUS.NEW])

        # get
        request = RequestFactory().get('/cancel/')
        request.user = User(username='test', is_superuser=True)
        response = view(
            request, flow_cls=ActionsTestFlow, flow_task=ActionsTestFlow.task,
            process_pk=act.process.pk, task_pk=task.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.template_name,
                         ('tests/test_views_actions/actionstest/task_cancel.html',
                          'tests/test_views_actions/actionstest/task_cancel.html',
                          'viewflow/flow/task_cancel.html',
                          'viewflow/flow/task_action.html'))
        self.assertEqual(response.context_data['activation'].process, act.process)

        # post
        request = RequestFactory().post('/cancel/', {'run_action': 1})
        request.user = User(username='test', is_superuser=True)
        response = view(
            request, flow_cls=ActionsTestFlow, flow_task=ActionsTestFlow.start,
            process_pk=act.process.pk, task_pk=task.pk)
        task.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(task.status, STATUS.CANCELED)
        self.assertIsNotNone(task.finished)

    def test_task_perform_view(self):
        act = ActionsTestFlow.start.run()
        view = actions.PerformView.as_view()
        if_gate = Task.objects.create(process=act.process, flow_task=ActionsTestFlow.if_gate)

        # get
        request = RequestFactory().get('/perform/')
        request.user = User(username='test', is_superuser=True)
        response = view(
            request, flow_cls=ActionsTestFlow, flow_task=ActionsTestFlow.if_gate,
            process_pk=act.process.pk, task_pk=if_gate.pk)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.template_name,
                         ('tests/test_views_actions/actionstest/if_gate_execute.html',
                          'tests/test_views_actions/actionstest/task_execute.html',
                          'viewflow/flow/task_execute.html',
                          'viewflow/flow/task_action.html'))
        self.assertEqual(response.context_data['activation'].process, act.process)

        # post
        request = RequestFactory().post('/perform/', {'run_action': 1})
        request.user = User(username='test', is_superuser=True)
        response = view(
            request, flow_cls=ActionsTestFlow, flow_task=ActionsTestFlow.if_gate,
            process_pk=act.process.pk, task_pk=if_gate.pk)
        if_gate.refresh_from_db()
        if_gate.process.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(if_gate.status, STATUS.DONE)
        self.assertIsNotNone(if_gate.finished)

    def test_task_activate_next_view(self):
        act = ActionsTestFlow.start.run()
        view = actions.ActivateNextView.as_view()
        task = act.process.get_task(ActionsTestFlow.task, status=[STATUS.NEW])
        task.finished = timezone.now()
        task.status = STATUS.DONE
        task.save()

        # get
        request = RequestFactory().get('/activate_next/')
        request.user = User(username='test', is_superuser=True)
        response = view(
            request, flow_cls=ActionsTestFlow, flow_task=ActionsTestFlow.task,
            process_pk=act.process.pk, task_pk=task.pk)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.template_name,
                         ('tests/test_views_actions/actionstest/task_activate_next.html',
                          'tests/test_views_actions/actionstest/task_activate_next.html',
                          'viewflow/flow/task_activate_next.html',
                          'viewflow/flow/task_action.html'))
        self.assertEqual(response.context_data['activation'].process, act.process)

        # post
        request = RequestFactory().post('/activate_next/', {'run_action': 1})
        request.user = User(username='test', is_superuser=True)
        response = view(
            request, flow_cls=ActionsTestFlow, flow_task=ActionsTestFlow.task,
            process_pk=act.process.pk, task_pk=task.pk)
        task.refresh_from_db()
        task.process.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(task.process.status, STATUS.DONE)

    def test_task_unassign_view(self):
        # prepare assigned task
        user = User.objects.create(username='test', is_superuser=True)
        view = UnassignView.as_view()

        act = ActionsTestFlow.start.run()
        task = act.process.get_task(ActionsTestFlow.task, status=[STATUS.NEW])
        task.activate().assign(user)

        # get
        request = RequestFactory().get('/unassign/')
        request.user = user
        response = view(
            request, flow_cls=ActionsTestFlow, flow_task=ActionsTestFlow.task,
            process_pk=act.process.pk, task_pk=task.pk)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.template_name,
                         ('tests/test_views_actions/actionstest/task_unassign.html',
                          'tests/test_views_actions/actionstest/task_unassign.html',
                          'viewflow/flow/task_unassign.html',
                          'viewflow/flow/task_action.html'))
        self.assertEqual(response.context_data['activation'].process, act.process)

        # post
        request = RequestFactory().post('/unassign/', {'run_action': 1})
        request.user = user
        response = view(
            request, flow_cls=ActionsTestFlow, flow_task=ActionsTestFlow.task,
            process_pk=act.process.pk, task_pk=task.pk)
        task.refresh_from_db()
        task.process.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(task.process.status, STATUS.NEW)


class ActionsTestFlow(Flow):
    start = flow.StartFunction().Next(this.task)
    if_gate = flow.If(lambda p: True).OnTrue(this.end).OnFalse(this.end)
    task = flow.View(ProcessView, fields=[]).Next(this.end)
    end = flow.End()


urlpatterns = [
    url(r'^test/', include([
        ActionsTestFlow.instance.urls,
        url('^$', list_views.ProcessListView.as_view(), name='index'),
        url('^tasks/$', list_views.TaskListView.as_view(), name='tasks'),
        url('^queue/$', list_views.QueueListView.as_view(), name='queue'),
        url('^details/(?P<process_pk>\d+)/$', list_views.ProcessDetailView.as_view(), name='details'),
    ], namespace=ActionsTestFlow.instance.namespace), {'flow_cls': ActionsTestFlow})
]

try:
    from django.test import override_settings
    Test = override_settings(ROOT_URLCONF=__name__)(Test)
except ImportError:
    """
    django 1.6
    """
    Test.urls = __name__
