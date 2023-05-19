from django.utils.translation import gettext_lazy as _
from unittest import TestCase
from viewflow import fsm, this
from .test_fsm__basics import Publication, ReviewState


class GuestPublication(Publication):
    @Publication.state.transition(
        source=ReviewState.NEW, target=ReviewState.APPROVED, permission=this.is_approver
    )
    def approve(self):
        pass

    @Publication.state.transition(
        source=ReviewState.NEW, target=ReviewState.REJECTED, permission=this.is_approver
    )
    def reject(self):
        pass

    @Publication.state.transition(
        source=ReviewState.HIDDEN,
        target=ReviewState.PUBLISHED,
        permission=this.is_superuser,
    )
    @Publication.state.transition(
        source=ReviewState.APPROVED, target=ReviewState.PUBLISHED
    )
    def publish(self):
        pass

    @Publication.state.transition(
        source=fsm.State.ANY, target=ReviewState.HIDDEN, conditions=[this.is_short]
    )
    def hide(self):
        pass

    @Publication.state.super()
    def remove(self):
        super().remove.original()

    def is_superuser(self, user):
        return user.is_superuser

    def is_approver(self, user):
        return user.is_staff

    is_approver.unmet_message = _("You have no staff rights")

    def is_short(self):
        text_length = len(self.text)
        return fsm.State.UNMET(
            text_length < 1000,
            _("Review is too shot, add %d symbols") % 1000 - text_length,
        )


class Test(TestCase):
    def setUp(self):
        self.publication = GuestPublication(text="test publication")
        self.assertEqual(self.publication.state, ReviewState.NEW)

    def test_method_transitions_list(self):
        transitions = {
            (transition.source, transition.target)
            for transition in self.publication.publish.get_transitions()
        }
        self.assertEqual(
            {
                (ReviewState.APPROVED, ReviewState.PUBLISHED),
                (ReviewState.HIDDEN, ReviewState.PUBLISHED),
            },
            transitions,
        )

    def test_field_transitions(self):
        transitions = {
            (transition.source, transition.target)
            for transitions in GuestPublication.state.get_transitions().values()
            for transition in transitions
        }
        self.assertEqual(
            {
                (ReviewState.NEW, ReviewState.APPROVED),
                (ReviewState.NEW, ReviewState.REJECTED),
                (ReviewState.APPROVED, ReviewState.PUBLISHED),
                (ReviewState.HIDDEN, ReviewState.PUBLISHED),
                (fsm.State.ANY, ReviewState.HIDDEN),
                (fsm.State.ANY, ReviewState.REMOVED),
            },
            transitions,
        )

    def test_redefined_transition_failed(self):
        self.assertRaises(fsm.TransitionNotAllowed, self.publication.publish)

    def test_approvement_workflow_succeed(self):
        self.publication.approve()
        self.assertEqual(self.publication.state, ReviewState.APPROVED)

        self.publication.publish()
        self.assertEqual(self.publication.state, ReviewState.PUBLISHED)

        self.publication.remove()
        self.assertEqual(self.publication.state, ReviewState.REMOVED)

    def test_rejection_workflow_succeed(self):
        self.publication.reject()
        self.assertEqual(self.publication.state, ReviewState.REJECTED)

        self.assertRaises(fsm.TransitionNotAllowed, self.publication.publish)

    def test_transition_permission(self):
        pass

    def test_transition_condition(self):
        pass
