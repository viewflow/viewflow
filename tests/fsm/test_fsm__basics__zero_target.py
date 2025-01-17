from unittest import TestCase
from viewflow import fsm


class ReviewState:
    ZERO = 0
    NEW = 1
    REMOVED = 2


class Publication:
    state = fsm.State(ReviewState, default=ReviewState.NEW)

    @state.transition(source=ReviewState.NEW, target=ReviewState.ZERO)
    def reset(self):
        pass

    @state.transition(source=fsm.State.ANY, target=ReviewState.REMOVED)
    def remove(self):
        pass


class TestStateValueZero(TestCase):
    def setUp(self):
        self.publication = Publication()
        self.assertEqual(self.publication.state, ReviewState.NEW)

    def test_transition_to_zero_state(self):
        self.publication.reset()
        self.assertEqual(self.publication.state, ReviewState.ZERO)

    def test_any_transition_to_removed(self):
        self.publication.remove()
        self.assertEqual(self.publication.state, ReviewState.REMOVED)
