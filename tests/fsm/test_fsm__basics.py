from unittest import TestCase
from viewflow import fsm
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class ReviewState(TextChoices):  # noqa:D100
    NEW = 'NEW', _('New')
    APPROVED = 'APPROVED', _('Approved')
    REJECTED = 'REJECTED', _('Rejected')
    PUBLISHED = 'PUBLISHED', _('Published')
    HIDDEN = 'HIDDEN', _('Hidden')
    REMOVED = 'REMOVED', _('Removed')


class Publication(object):  # noqa:D100
    stage = fsm.State(ReviewState, default=ReviewState.NEW)

    def __init__(self, text):
        self.text = text

    @stage.transition(
        source=ReviewState.NEW,
        target=ReviewState.PUBLISHED
    )
    def publish(self):
        pass

    @stage.transition(
        source=fsm.State.ANY,
        target=ReviewState.REMOVED
    )
    def remove(self):
        pass

    @stage.transition(
        source=ReviewState.PUBLISHED,
        target=ReviewState.HIDDEN
    )
    def hide(self):
        pass


# REST
# Admin
# Viewset


class Test(TestCase):  # noqa:D100
    def setUp(self):
        self.publication = Publication(text='test publication')
        self.assertEqual(self.publication.stage, ReviewState.NEW)

    def test_direct_modifications_not_allowed(self):
        with self.assertRaises(AttributeError):
            self.publication.stage = ReviewState.REMOVED

    def test_method_transitions_list(self):
        transitions = {
            (transition.source, transition.target)
            for transition in self.publication.publish.get_transitions()
        }
        self.assertEqual({
            (ReviewState.NEW, ReviewState.PUBLISHED),
        }, transitions)

    def test_field_transitions(self):
        transitions = {
            (transition.source, transition.target)
            for transitions in Publication.stage.get_transitions().values()
            for transition in transitions
        }
        self.assertEqual({
            (ReviewState.NEW, ReviewState.PUBLISHED),
            (ReviewState.PUBLISHED, ReviewState.HIDDEN),
            (fsm.State.ANY, ReviewState.REMOVED),
        }, transitions)

    def test_allowed_transitions_succeed(self):
        self.publication.publish()
        self.assertEqual(self.publication.stage, ReviewState.PUBLISHED)

        self.publication.remove()
        self.assertEqual(self.publication.stage, ReviewState.REMOVED)

    def test_prohibited_transition_failed(self):
        self.assertRaises(fsm.TransitionNotAllowed, self.publication.hide)

    def test_transitions_can_proceed(self):
        self.assertTrue(self.publication.publish.can_proceed())
        self.assertTrue(self.publication.remove.can_proceed())
        self.assertFalse(self.publication.hide.can_proceed())

        self.publication.publish()
        self.assertFalse(self.publication.publish.can_proceed())
        self.assertTrue(self.publication.remove.can_proceed())
        self.assertTrue(self.publication.hide.can_proceed())
