"""Test for permission check."""

from django.contrib.auth.models import User
from django.test import TestCase
from viewflow import this
from viewflow.fsm import State
from .test_fsm__basics import ReviewState


class _Publication(object):
    stage = State(ReviewState, default=ReviewState.NEW)

    @stage.transition(
        source=ReviewState.NEW,
        target=ReviewState.REMOVED,
        permission=this.can_remove_review
    )
    def remove(self):
        pass

    def can_remove_review(self, user):
        return State.CONDITION(user.is_staff, unmet="Only staff users can delete reviews")


class _Test(TestCase):
    def setUp(self):
        self.privileged_user = User.objects.create(
            username='privileged',
            is_staff=True
        )

        self.unprivileged_user = User.objects.create(
            username='unprivileged',
            is_staff=False
        )

    def test_callable_permission(self):
        publication = _Publication()

        self.assertTrue(
            publication.remove.has_perm(self.privileged_user)
        )

        self.assertFalse(
            publication.remove.has_perm(self.unprivileged_user)
        )
