from django.contrib.auth.models import User

from django.conf.urls import patterns, include, url
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from viewflow import flow
from viewflow.base import Flow, this
from viewflow.models import Task

from unit.helpers import get_default_form_data


@flow.flow_view()
def perform_task(request, activation):
    raise NotImplementedError


class RestrictedUserFlow(Flow):
    start = flow.Start().Activate(this.specific_user)

    specific_user = flow.View(perform_task).Next(this.callable_user) \
        .Assign(username='employee')

    callable_user = flow.View(perform_task).Next(this.permission) \
        .Assign(lambda p: User.objects.get(username='employee'))

    permission = flow.View(perform_task).Next(this.end) \
        .Permission('unit.restricted_permission_flow__view')

    end = flow.End()


urlpatterns = patterns('', url('^', include(RestrictedUserFlow.instance.urls)))


class TestRestrictedUserFlow(TestCase):
    urls = 'unit.tests.test_task_assign'

    def setUp(self):
        self.user, _ = User.objects.get_or_create(username='employee')

    def test_view_task_assigned_to_user(self):
        # start
        activation = RestrictedUserFlow.start.activation_cls()
        activation.initialize(RestrictedUserFlow.start)
        activation.prepare()
        data = get_default_form_data(activation.management_form)

        activation.initialize(RestrictedUserFlow.start)
        activation.prepare(data)
        activation.done(user=self.user)

        # start_task = flow_do(RestrictedUserFlow.start, self.client)
        # specific_user = flow_do(RestrictedUserFlow.view, self.client)

        # view
        #task = Task.objects.get(flow_task=RestrictedUserFlow.view)
        #self.assertEqual(Task.STATUS.ASSIGNED, task.status)
        #self.assertEqual(self.user, task.owner)

        #activation = RestrictedUserFlow.view.start(task)
        #self.assertTrue(RestrictedUserFlow.view.has_perm(self.user, task))


class TestRestrictedCallableUserFlow(TestCase):
    def setUp(self):
        self.user, _ = User.objects.get_or_create(username='employee')

    def _test_view_task_assigned_to_user(self):
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

    def _test_view_task_permission_check_and_assignment(self):
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
