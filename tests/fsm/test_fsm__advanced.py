"""FSM tests for advanced source/target options"""

from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from viewflow.fsm import State
from viewflow.utils import DEFAULT
from .test_fsm__basics import ReviewState


class Publication(object):
    stage = State(ReviewState, default=ReviewState.NEW)

    def __init__(self, text):
        self.text = text

    @stage.transition(source=ReviewState.NEW)
    def notify(self):
        pass

    @stage.transition(
        source={ReviewState.NEW, ReviewState.HIDDEN}, target=ReviewState.PUBLISHED
    )
    def publish(self):
        pass

    @stage.transition(source=ReviewState.NEW, target=ReviewState.PUBLISHED)
    @stage.transition(
        source=ReviewState.PUBLISHED, target=ReviewState.NEW, label=_("Return to new")
    )
    def toggle(self):
        pass

    toggle.label = _("Toggle publication state")

    @stage.transition(source=ReviewState.PUBLISHED, target=ReviewState.REJECTED)
    def trash(self):
        if len(self.text) > 1000:
            self.hide()
        else:
            self.remove()

    @stage.transition(source=ReviewState.REJECTED, target=ReviewState.REMOVED)
    def remove(self):
        pass

    @stage.transition(source=ReviewState.REJECTED, target=ReviewState.HIDDEN)
    def hide(self):
        pass


class Test(TestCase):  # noqa: D101
    def test_no_target_transition(self):
        publication = Publication(text="test")
        publication.notify()
        self.assertEqual(publication.stage, ReviewState.NEW)

    def test_big_publication_process(self):
        publication = Publication(text="test" * 251)
        self.assertEqual(publication.stage, ReviewState.NEW)

        publication.publish()
        self.assertEqual(publication.stage, ReviewState.PUBLISHED)

        publication.trash()
        self.assertEqual(publication.stage, ReviewState.HIDDEN)

    def test_small_publication_process(self):
        publication = Publication(text="test" * 249)
        self.assertEqual(publication.stage, ReviewState.NEW)

        publication.publish()
        self.assertEqual(publication.stage, ReviewState.PUBLISHED)

        publication.trash()
        self.assertEqual(publication.stage, ReviewState.REMOVED)

    def test_available_transitions(self):
        self.assertEqual(
            [
                (transition.target, transition.slug)
                for transition in Publication.stage.get_outgoing_transitions(
                    ReviewState.NEW
                )
            ],
            [
                (DEFAULT, "notify"),
                (ReviewState.PUBLISHED, "publish"),
                (ReviewState.PUBLISHED, "toggle"),
            ],
        )

        self.assertEqual(
            [
                (transition.target, transition.slug)
                for transition in Publication.stage.get_outgoing_transitions(
                    ReviewState.PUBLISHED
                )
            ],
            [(ReviewState.NEW, "toggle"), (ReviewState.REJECTED, "trash")],
        )

        self.assertEqual(
            [
                (transition.target, transition.slug)
                for transition in Publication.stage.get_outgoing_transitions(
                    ReviewState.REJECTED
                )
            ],
            [(ReviewState.HIDDEN, "hide"), (ReviewState.REMOVED, "remove")],
        )
