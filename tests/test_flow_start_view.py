import pytz
from datetime import datetime

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from viewflow import flow
from viewflow.base import Flow
from viewflow.activation import STATUS
from viewflow.flow import start_view


class Test(TestCase):
    def init_node(self, node, flow_cls=None, name='test_node'):
        node.flow_cls = flow_cls or Flow
        node.name = name
        return node

    def test_flow_start_view_decorator(self):
        @start_view.flow_start_view()
        def start_test_view(request, activation):
            activation.prepare()
            activation.done()
            return activation

        act = start_test_view(None, Flow, self.init_node(flow.Start()))
        self.assertEqual(act.task.status, STATUS.DONE)

    def test_managed_start_view_activation_prepare(self):
        act = start_view.ManagedStartViewActivation()
        act.initialize(self.init_node(flow.Start()), None)

        act.prepare(data={'_viewflow_activation-started': '1970-01-01'})
        self.assertEqual(act.task.started, datetime(1970, 1, 1, tzinfo=pytz.UTC))

    def test_start_can_execute_owner_permission(self):
        user = User.objects.create(username="test")
        user_type = ContentType.objects.get(app_label="auth", model="user")
        permission = Permission.objects.create(
            name='existing_perm', content_type=user_type, codename='existing_perm')
        user.user_permissions.add(permission)

        flow_task = self.init_node(flow.Start().Permission('auth.existing_perm'))
        self.assertTrue(flow_task.can_execute(user))

        flow_task = self.init_node(flow.Start().Permission(lambda user: True))
        self.assertTrue(flow_task.can_execute(user))

        flow_task = self.init_node(flow.Start().Permission('auth.unknown_perm'))
        self.assertFalse(flow_task.can_execute(user))

        flow_task = self.init_node(flow.Start().Permission(lambda user: False))
        self.assertFalse(flow_task.can_execute(user))
