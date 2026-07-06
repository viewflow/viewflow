from unittest import TestCase
from viewflow import fsm
from django.db.models import TextChoices
from django.utils.translation import gettext_lazy as _


class ReviewState(TextChoices):  # noqa:D100
    NEW = "NEW", _("New")
    APPROVED = "APPROVED", _("Approved")
    REJECTED = "REJECTED", _("Rejected")
    PUBLISHED = "PUBLISHED", _("Published")
    HIDDEN = "HIDDEN", _("Hidden")
    REMOVED = "REMOVED", _("Removed")


class Publication(object):  # noqa:D100
    state = fsm.State(ReviewState, default=ReviewState.NEW)

    def __init__(self, text):
        self.text = text

    @state.transition(source=ReviewState.NEW, target=ReviewState.PUBLISHED)
    def publish(self):
        pass

    @state.transition(source=fsm.State.ANY, target=ReviewState.REMOVED)
    def remove(self):
        pass

    @state.transition(source=ReviewState.PUBLISHED, target=ReviewState.HIDDEN)
    def hide(self):
        pass

    @state.transition(
        source=ReviewState.NEW,
        target=ReviewState.APPROVED,
        conditions=[lambda instance: False],
    )
    def approve(self):
        pass


class FalsyPublication(Publication):  # noqa:D100
    # A container-like instance that is falsy (len(self) == 0) but not
    # None. The descriptors must still treat it as a real instance.
    def __len__(self):
        return 0


# REST
# Admin
# Viewset


class Test(TestCase):  # noqa:D100
    def setUp(self):
        self.publication = Publication(text="test publication")
        self.assertEqual(self.publication.state, ReviewState.NEW)

    def test_direct_modifications_not_allowed(self):
        with self.assertRaises(AttributeError):
            self.publication.state = ReviewState.REMOVED

    def test_method_transitions_list(self):
        transitions = {
            (transition.source, transition.target)
            for transition in self.publication.publish.get_transitions()
        }
        self.assertEqual(
            {
                (ReviewState.NEW, ReviewState.PUBLISHED),
            },
            transitions,
        )

    def test_field_transitions(self):
        transitions = {
            (transition.source, transition.target)
            for transitions in Publication.state.get_transitions().values()
            for transition in transitions
        }
        self.assertEqual(
            {
                (ReviewState.NEW, ReviewState.PUBLISHED),
                (ReviewState.PUBLISHED, ReviewState.HIDDEN),
                (fsm.State.ANY, ReviewState.REMOVED),
                (ReviewState.NEW, ReviewState.APPROVED),
            },
            transitions,
        )

    def test_allowed_transitions_succeed(self):
        self.publication.publish()
        self.assertEqual(self.publication.state, ReviewState.PUBLISHED)

        self.publication.remove()
        self.assertEqual(self.publication.state, ReviewState.REMOVED)

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

    def test_can_proceed_without_checking_conditions(self):
        # INVERTED: can_proceed(check_conditions=False) returned False even
        # when a matching transition existed -- it should skip the
        # condition check, not treat "don't check conditions" as "no
        # transition available".
        self.assertFalse(self.publication.approve.can_proceed())
        self.assertTrue(self.publication.approve.can_proceed(check_conditions=False))

        # A genuinely absent transition must still report unavailable
        # regardless of check_conditions.
        self.assertFalse(self.publication.hide.can_proceed(check_conditions=False))


class TestFalsyInstance(TestCase):  # noqa:D100
    # `if instance:` (instead of `if instance is not None:`) in the
    # descriptors meant a falsy-but-real instance fell through to the
    # class-level (unbound) branch instead of the instance-bound one.
    def setUp(self):
        self.publication = FalsyPublication(text="empty")
        self.assertFalse(self.publication)  # sanity: falsy, but not None

    def test_state_read_on_falsy_instance(self):
        self.assertEqual(self.publication.state, ReviewState.NEW)

    def test_transition_call_on_falsy_instance(self):
        self.publication.publish()
        self.assertEqual(self.publication.state, ReviewState.PUBLISHED)
