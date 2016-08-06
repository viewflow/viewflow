import pytz
from datetime import datetime

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, RequestFactory

from viewflow import flow
from viewflow.base import Flow
from viewflow.activation import STATUS
from viewflow.decorators import flow_view
from viewflow.flow.activation import ManagedViewActivation
from viewflow.models import Process, Task


class Test(TestCase):
    def test_flow_view_decorator(self):
        process = Process.objects.create(flow_class=TaskTestFlow)
        task = Task.objects.create(process=process, flow_task=TaskTestFlow.task)

        @flow_view
        def test_view(request):
            request.activation.assign()
            request.activation.prepare()
            request.activation.done()
            return request.activation

        request = RequestFactory().get('')
        act = test_view(request, TaskTestFlow, TaskTestFlow.task, process.pk, task.pk)
        self.assertEqual(act.task.status, STATUS.DONE)

    def test_managed_view_activation_prepare(self):
        process = Process.objects.create(flow_class=TaskTestFlow)
        task = Task.objects.create(process=process, flow_task=TaskTestFlow.task)

        act = ManagedViewActivation()
        act.initialize(TaskTestFlow.task, task)

        act.assign()
        act.prepare(data={'_viewflow_activation-started': '1970-01-01'})
        self.assertEqual(act.task.started, datetime(1970, 1, 1, tzinfo=pytz.UTC))

    def test_view_permissins_calc(self):
        user = User.objects.create(username="test")
        process = Process.objects.create(flow_class=TaskTestFlow)
        task = Task.objects.create(process=process, flow_task=TaskTestFlow.task)

        flow_task = flow.View(lambda request: None).Assign(lambda p: "TEST USER")
        self.assertEqual(flow_task.calc_owner(task), "TEST USER")

        flow_task = flow.View(lambda request: None).Assign({'username': 'test'})
        self.assertEqual(flow_task.calc_owner(task), user)

        flow_task = flow.View(lambda request: None).Permission("TEST PERM")
        self.assertEqual(flow_task.calc_owner_permission(task), "TEST PERM")

        flow_task = flow.View(lambda request: None).Permission(lambda p: "TEST PERM")
        self.assertEqual(flow_task.calc_owner_permission(task), "TEST PERM")

    def test_view_can_assign(self):
        user = User.objects.create(username="test")
        user_type = ContentType.objects.get(app_label="auth", model="user")
        permission = Permission.objects.create(
            name='existing_perm', content_type=user_type, codename='existing_perm')
        user.user_permissions.add(permission)
        process = Process.objects.create(flow_class=TaskTestFlow)

        flow_task = flow.View(lambda request: None).Permission('auth.existing_perm')
        task = Task.objects.create(process=process, flow_task=TaskTestFlow.task,
                                   owner_permission='auth.existing_perm')
        self.assertTrue(flow_task.can_assign(user, task))

        flow_task = flow.View(lambda request: None).Permission('auth.unknown_perm')
        task = Task.objects.create(process=process, flow_task=TaskTestFlow.task,
                                   owner_permission='auth.unknown_perm')
        self.assertFalse(flow_task.can_assign(user, task))


class TaskTestFlow(Flow):
    task = flow.View(lambda request: None)
