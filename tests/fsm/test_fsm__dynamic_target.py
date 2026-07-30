"""Tests for @transition(target=State.RETURN_VALUE(...)/State.GET_STATE(...))."""

from unittest import TestCase
from viewflow import fsm
from viewflow.fsm import State


class _ReturnValueFlow:
    state = fsm.State(states=["new", "published", "for_moderators"], default="new")

    def __init__(self):
        self.state_when_called = None

    @state.transition(
        source="new", target=State.RETURN_VALUE("published", "for_moderators")
    )
    def publish(self, is_public):
        # The state hasn't changed yet -- RETURN_VALUE can only be resolved
        # once this method returns.
        self.state_when_called = self.state
        return "published" if is_public else "for_moderators"

    @state.transition(source="new", target=State.RETURN_VALUE())
    def publish_unrestricted(self, next_state):
        return next_state


class TestReturnValue(TestCase):
    def test_state_set_from_return_value(self):
        flow = _ReturnValueFlow()
        flow.publish(is_public=True)
        self.assertEqual(flow.state, "published")

    def test_other_branch(self):
        flow = _ReturnValueFlow()
        flow.publish(is_public=False)
        self.assertEqual(flow.state, "for_moderators")

    def test_state_unchanged_while_method_runs(self):
        flow = _ReturnValueFlow()
        flow.publish(is_public=True)
        self.assertEqual(flow.state_when_called, "new")

    def test_return_value_outside_declared_states_raises(self):
        class _StrictFlow:
            state = fsm.State(
                states=["new", "published", "for_moderators"], default="new"
            )

            @state.transition(
                source="new",
                target=State.RETURN_VALUE("published", "for_moderators"),
            )
            def publish(self, next_state):
                return next_state

        flow = _StrictFlow()
        with self.assertRaises(fsm.InvalidTargetState) as ctx:
            flow.publish("removed")  # not in the declared allowed set

        exc = ctx.exception
        self.assertEqual(exc.allowed_states, ("published", "for_moderators"))
        self.assertEqual(exc.target, "removed")

    def test_unrestricted_return_value_accepts_anything(self):
        flow = _ReturnValueFlow()
        flow.publish_unrestricted("anything")
        self.assertEqual(flow.state, "anything")

    def test_invalid_target_state_does_not_change_state(self):
        class _StrictFlow:
            state = fsm.State(states=["new", "published"], default="new")

            @state.transition(source="new", target=State.RETURN_VALUE("published"))
            def publish(self, value):
                return value

        flow = _StrictFlow()
        with self.assertRaises(fsm.InvalidTargetState):
            flow.publish("not-allowed")
        self.assertEqual(flow.state, "new")

    def test_invalid_target_state_is_a_transition_not_allowed(self):
        class _StrictFlow:
            state = fsm.State(states=["new", "published"], default="new")

            @state.transition(source="new", target=State.RETURN_VALUE("published"))
            def publish(self, value):
                return value

        flow = _StrictFlow()
        with self.assertRaises(fsm.TransitionNotAllowed):
            flow.publish("not-allowed")


def _decide_review_target(instance, approved):
    return "approved" if approved else "rejected"


class _GetStateFlow:
    state = fsm.State(states=["new", "approved", "rejected"], default="new")

    def __init__(self):
        self.state_when_called = None

    @state.transition(
        source="new",
        target=State.GET_STATE(_decide_review_target, states=["approved", "rejected"]),
    )
    def review(self, approved):
        # Unlike RETURN_VALUE, GET_STATE is resolved up front -- the method
        # body already observes the new state.
        self.state_when_called = self.state
        return "some unrelated return value"


class TestGetState(TestCase):
    def test_state_set_from_computed_target(self):
        flow = _GetStateFlow()
        flow.review(approved=True)
        self.assertEqual(flow.state, "approved")

    def test_other_branch(self):
        flow = _GetStateFlow()
        flow.review(approved=False)
        self.assertEqual(flow.state, "rejected")

    def test_state_already_updated_while_method_runs(self):
        flow = _GetStateFlow()
        flow.review(approved=True)
        self.assertEqual(flow.state_when_called, "approved")

    def test_computed_target_outside_declared_states_raises(self):
        class _Flow:
            state = fsm.State(states=["new", "approved"], default="new")

            @state.transition(
                source="new",
                target=State.GET_STATE(
                    lambda instance: "unknown-state", states=["approved"]
                ),
            )
            def review(self):
                pass

        flow = _Flow()
        with self.assertRaises(fsm.InvalidTargetState):
            flow.review()
        # Rejected before the state was ever touched.
        self.assertEqual(flow.state, "new")

    def test_method_body_does_not_run_when_computed_target_is_invalid(self):
        calls = []

        class _Flow:
            state = fsm.State(states=["new", "approved"], default="new")

            @state.transition(
                source="new",
                target=State.GET_STATE(
                    lambda instance: "unknown-state", states=["approved"]
                ),
            )
            def review(self):
                calls.append(1)

        flow = _Flow()
        with self.assertRaises(fsm.InvalidTargetState):
            flow.review()
        self.assertEqual(calls, [])

    def test_unrestricted_get_state_accepts_anything(self):
        class _Flow:
            state = fsm.State(states=["new", "anything"], default="new")

            @state.transition(
                source="new", target=State.GET_STATE(lambda instance: "anything")
            )
            def review(self):
                pass

        flow = _Flow()
        flow.review()
        self.assertEqual(flow.state, "anything")


class TestRollbackOnException(TestCase):
    def test_return_value_target_rolls_back_on_exception(self):
        class _Flow:
            state = fsm.State(states=["new", "published"], default="new")

            @state.transition(source="new", target=State.RETURN_VALUE("published"))
            def publish(self):
                raise RuntimeError("boom")

        flow = _Flow()
        with self.assertRaises(RuntimeError):
            flow.publish()
        self.assertEqual(flow.state, "new")

    def test_get_state_target_rolls_back_on_exception(self):
        class _Flow:
            state = fsm.State(states=["new", "approved"], default="new")

            @state.transition(
                source="new", target=State.GET_STATE(lambda instance: "approved")
            )
            def review(self):
                raise RuntimeError("boom")

        flow = _Flow()
        with self.assertRaises(RuntimeError):
            flow.review()
        self.assertEqual(flow.state, "new")


class TestChart(TestCase):
    def test_return_value_charts_an_edge_per_declared_state(self):
        output = fsm.chart(_ReturnValueFlow.state)
        self.assertIn('"new" -> "published"', output)
        self.assertIn('"new" -> "for_moderators"', output)

    def test_undeclared_return_value_charts_no_edge(self):
        output = fsm.chart(_ReturnValueFlow.state)
        self.assertNotIn("publish_unrestricted", output)

    def test_get_state_charts_an_edge_per_declared_state(self):
        output = fsm.chart(_GetStateFlow.state)
        self.assertIn('"new" -> "approved"', output)


class TestOutgoingTransitionsWithAnySource(TestCase):
    """A ``State.ANY``-sourced dynamic target is excluded from
    ``get_outgoing_transitions(state)`` only for a state it declares as a
    possible landing spot -- same rule as a plain target, now shared via
    ``Transition.declared_targets()`` instead of comparing the raw marker.
    """

    class _Flow:
        state = fsm.State(states=["new", "approved", "rejected"], default="new")

        @state.transition(
            source=State.ANY,
            target=State.GET_STATE(
                _decide_review_target, states=["approved", "rejected"]
            ),
        )
        def review(self, approved):
            pass

        @state.transition(source=State.ANY, target=State.RETURN_VALUE())
        def force(self, next_state):
            return next_state

    def test_declared_dynamic_target_excluded_for_its_own_state(self):
        transitions = self._Flow.state.get_outgoing_transitions("approved")
        slugs = {t.slug for t in transitions}
        self.assertNotIn("review", slugs)

    def test_declared_dynamic_target_included_for_other_states(self):
        transitions = self._Flow.state.get_outgoing_transitions("new")
        slugs = {t.slug for t in transitions}
        self.assertIn("review", slugs)

    def test_unrestricted_dynamic_target_always_included(self):
        # force() declares no allowed_states, so its real target is unknown
        # ahead of a call -- it's listed as outgoing from every state,
        # including one it might, at runtime, just return you to.
        for current_state in ("new", "approved", "rejected"):
            transitions = self._Flow.state.get_outgoing_transitions(current_state)
            slugs = {t.slug for t in transitions}
            self.assertIn("force", slugs)
