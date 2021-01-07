from django.urls import include, re_path
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.urls import resolve
from django.utils import timezone

from viewflow import flow
from viewflow.base import Flow, this
from viewflow.activation import STATUS
from viewflow.models import Task
from viewflow.flow import views, viewset


class Test(TestCase):
    def test_process_cancel_view(self):
        act = ActionsTestFlow.start.run()
        view = views.CancelProcessView.as_view()

        # get
        request = RequestFactory().get('/cancel/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(request, flow_class=ActionsTestFlow, process_pk=act.process.pk)
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
        request.resolver_match = resolve('/test/')

        response = view(request, flow_class=ActionsTestFlow, process_pk=act.process.pk)
        act.process.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(act.process.status, STATUS.CANCELED)
        canceled_task = act.process.get_task(ActionsTestFlow.task, status=[STATUS.CANCELED])
        self.assertIsNotNone(canceled_task.finished)

    def test_task_undo_view(self):
        act = ActionsTestFlow.start.run()
        view = views.UndoTaskView.as_view()

        # prepare the process with cancelable start action
        task = act.process.get_task(ActionsTestFlow.task, status=[STATUS.NEW])
        act = task.activate()
        act.cancel()

        start = act.process.get_task(ActionsTestFlow.start, status=[STATUS.DONE])

        # get
        request = RequestFactory().get('/undo/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(
            request, flow_class=ActionsTestFlow, flow_task=ActionsTestFlow.start,
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
        request.resolver_match = resolve('/test/')

        response = view(
            request, flow_class=ActionsTestFlow, flow_task=ActionsTestFlow.start,
            process_pk=act.process.pk, task_pk=start.pk)
        start.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(start.status, STATUS.CANCELED)
        self.assertEqual(start.process.status, STATUS.CANCELED)
        self.assertIsNotNone(start.finished)

    def test_task_cancel_view(self):
        act = ActionsTestFlow.start.run()
        view = views.CancelTaskView.as_view()
        task = act.process.get_task(ActionsTestFlow.task, status=[STATUS.NEW])

        # get
        request = RequestFactory().get('/cancel/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(
            request, flow_class=ActionsTestFlow, flow_task=ActionsTestFlow.task,
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
        request.resolver_match = resolve('/test/')

        response = view(
            request, flow_class=ActionsTestFlow, flow_task=ActionsTestFlow.start,
            process_pk=act.process.pk, task_pk=task.pk)
        task.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(task.status, STATUS.CANCELED)
        self.assertIsNotNone(task.finished)

    def test_task_perform_view(self):
        act = ActionsTestFlow.start.run()
        view = views.PerformTaskView.as_view()
        if_gate = Task.objects.create(process=act.process, flow_task=ActionsTestFlow.if_gate)

        # get
        request = RequestFactory().get('/perform/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(
            request, flow_class=ActionsTestFlow, flow_task=ActionsTestFlow.if_gate,
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
        request.resolver_match = resolve('/test/')

        response = view(
            request, flow_class=ActionsTestFlow, flow_task=ActionsTestFlow.if_gate,
            process_pk=act.process.pk, task_pk=if_gate.pk)
        if_gate.refresh_from_db()
        if_gate.process.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(if_gate.status, STATUS.DONE)
        self.assertIsNotNone(if_gate.finished)

    def test_task_activate_next_view(self):
        act = ActionsTestFlow.start.run()
        view = views.ActivateNextTaskView.as_view()
        task = act.process.get_task(ActionsTestFlow.task, status=[STATUS.NEW])
        task.finished = timezone.now()
        task.status = STATUS.DONE
        task.save()

        # get
        request = RequestFactory().get('/activate_next/')
        request.user = User(username='test', is_superuser=True)
        request.resolver_match = resolve('/test/')

        response = view(
            request, flow_class=ActionsTestFlow, flow_task=ActionsTestFlow.task,
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
        request.resolver_match = resolve('/test/')

        response = view(
            request, flow_class=ActionsTestFlow, flow_task=ActionsTestFlow.task,
            process_pk=act.process.pk, task_pk=task.pk)
        task.refresh_from_db()
        task.process.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(task.process.status, STATUS.DONE)

    def test_task_unassign_view(self):
        # prepare assigned task
        user = User.objects.create(username='test', is_superuser=True)
        view = views.UnassignTaskView.as_view()

        act = ActionsTestFlow.start.run()
        task = act.process.get_task(ActionsTestFlow.task, status=[STATUS.NEW])
        task.activate().assign(user)

        # get
        request = RequestFactory().get('/unassign/')
        request.user = user
        request.resolver_match = resolve('/test/')

        response = view(
            request, flow_class=ActionsTestFlow, flow_task=ActionsTestFlow.task,
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
        request.resolver_match = resolve('/test/')

        response = view(
            request, flow_class=ActionsTestFlow, flow_task=ActionsTestFlow.task,
            process_pk=act.process.pk, task_pk=task.pk)
        task.refresh_from_db()
        task.process.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(task.process.status, STATUS.NEW)


class ActionsTestFlow(Flow):
    start = flow.StartFunction().Next(this.task)
    if_gate = flow.If(lambda p: True).Then(this.end).Else(this.end)
    task = flow.View(views.UpdateProcessView, fields=[]).Next(this.end)
    end = flow.End()


urlpatterns = [
    re_path(r'^test/', include((viewset.FlowViewSet(ActionsTestFlow).urls, 'actionstest')))
]

try:
    from django.test import override_settings
    Test = override_settings(ROOT_URLCONF=__name__)(Test)
except ImportError:
    """
    django 1.6
    """
    Test.urls = __name__
