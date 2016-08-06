import pytz
from datetime import datetime

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, RequestFactory

from viewflow import flow
from viewflow.base import Flow
from viewflow.activation import STATUS
from viewflow.decorators import flow_start_view
from viewflow.flow.activation import ManagedStartViewActivation


class Test(TestCase):
    def init_node(self, node, flow_class=None, name='test_node'):
        node.flow_class = flow_class or Flow
        node.name = name
        return node

    def test_flow_start_view_decorator(self):
        @flow_start_view
        def start_test_view(request):
            request.activation.prepare()
            request.activation.done()
            return request.activation

        request = RequestFactory().get('/start/')
        act = start_test_view(request, Flow, self.init_node(flow.Start()))
        self.assertEqual(act.task.status, STATUS.DONE)

    def test_managed_start_view_activation_prepare(self):
        act = ManagedStartViewActivation()
        act.initialize(self.init_node(flow.Start()), None)

        act.prepare(data={'_viewflow_activation-started': '1970-01-01'})
        self.assertEqual(act.task.started, datetime(1970, 1, 1, tzinfo=pytz.UTC))

    def test_start_can_execute(self):
        user = User.objects.create(username="test")
        user_type = ContentType.objects.get(app_label="auth", model="user")
        permission = Permission.objects.create(
            name='existing_perm', content_type=user_type, codename='existing_perm')
        user.user_permissions.add(permission)

        flow_task = self.init_node(flow.Start().Available(lambda user: True))
        self.assertTrue(flow_task.can_execute(user))

        flow_task = self.init_node(flow.Start().Available(lambda user: False))
        self.assertFalse(flow_task.can_execute(user))

        flow_task = self.init_node(flow.Start().Permission('auth.existing_perm'))
        self.assertTrue(flow_task.can_execute(user))

        flow_task = self.init_node(flow.Start().Permission('auth.unknown_perm'))
        self.assertFalse(flow_task.can_execute(user))
