from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission
from django.test import TestCase

from viewflow.models import Task

from unit.flows import RestrictedUserFlow, RestrictedCallableUserFlow, RestrictedPermissionFlow
from unit.helpers import get_default_form_data


class TestRestrictedUserFlow(TestCase):
    def setUp(self):
        self.user, _ = User.objects.get_or_create(username='employee')

    def test_view_task_assigned_to_user(self):
        # start
        activation = RestrictedUserFlow.start.start()
        activation = RestrictedUserFlow.start.start(get_default_form_data(activation.form))
        RestrictedUserFlow.start.done(activation)

        # view
        task = Task.objects.get(flow_task=RestrictedUserFlow.view)
        self.assertEqual(Task.STATUS.ASSIGNED, task.status)
        self.assertEqual(self.user, task.owner)

        activation = RestrictedUserFlow.view.start(task)
        self.assertTrue(RestrictedUserFlow.view.has_perm(self.user, task))


class TestRestrictedCallableUserFlow(TestCase):
    def setUp(self):
        self.user, _ = User.objects.get_or_create(username='employee')

    def test_view_task_assigned_to_user(self):
        # start
        activation = RestrictedCallableUserFlow.start.start()
        activation = RestrictedCallableUserFlow.start.start(get_default_form_data(activation.form))
        RestrictedCallableUserFlow.start.done(activation)

        # view
        task = Task.objects.get(flow_task=RestrictedCallableUserFlow.view)
        self.assertEqual(Task.STATUS.ASSIGNED, task.status)
        self.assertEqual(self.user, task.owner)

        activation = RestrictedCallableUserFlow.view.start(task)
        self.assertTrue(RestrictedCallableUserFlow.view.has_perm(self.user, task))


class TestRestrictedPermissionFlow(TestCase):
    def setUp(self):
        content_type = ContentType.objects.get_by_natural_key('unit', 'testprocess')
        permission = Permission.objects.create(codename='restricted_permission_flow__view',
                                               name='Can do view task',
                                               content_type=content_type)
        self.user, _ = User.objects.get_or_create(username='employee')
        self.user.user_permissions.add(permission)

    def test_view_task_permission_check_and_assignment(self):
        # start
        activation = RestrictedPermissionFlow.start.start()
        activation = RestrictedPermissionFlow.start.start(get_default_form_data(activation.form))
        RestrictedPermissionFlow.start.done(activation)

        # view
        task = Task.objects.get(flow_task=RestrictedPermissionFlow.view)
        self.assertEqual(Task.STATUS.ACTIVATED, task.status)
        self.assertEqual('unit.restricted_permission_flow__view', task.owner_permission)

        activation = RestrictedPermissionFlow.view.start(task)
        self.assertTrue(RestrictedPermissionFlow.view.can_be_assigned(self.user, task))
        activation.assign(self.user)

        activation = RestrictedPermissionFlow.view.start(task)
        self.assertTrue(RestrictedPermissionFlow.view.has_perm(self.user, task))
