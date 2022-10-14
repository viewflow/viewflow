from django.contrib.auth.models import User
from django.test import TestCase

from viewflow import this
from viewflow.workflow import flow


class Test(TestCase):  # noqa: D101
    def setUp(self):
        pass

    def test_available_processes(self):
        pass

    def test_user_task_inbox(self):
        pass

    def test_user_task_queue(self):
        pass

    def test_user_task_archive(self):
        pass

    # TODO guardian permissions


class StaffOnlyFlow(flow.Flow):
    """ Flow available for staff users only."""

    start = flow.StartHandle(this.start_flow).Next(this.task)

    task = (
        flow.View(this.task_view)
        .Assign(this.get_task_user)
        .Next(this.end)
    )

    end = flow.End()

    def start_flow(self, activation, user=None):
        activation.process.data = {'user_pk': user.pk}

    def get_task_user(self, activation):
        User.object.get(pk=activation.process.data['user_pk'])

    def has_view_permission(self, user, obj=None):
        return user.is_staff


class PermissionSpecificFlow(flow.Flow):
    """ Flow available iff a user has specific permission."""
    start = flow.StartHandle(this.start_flow).Next(this.task)

    task = (
        flow.View(this.task_view)
        .Permission(auto_create=True)
        .Next(this.end)
    )

    end = flow.End()
