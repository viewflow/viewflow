from enum import Enum
from unittest import TestCase
from viewflow import fsm
from viewflow.fsm import State


class TestFlow:
    state = fsm.State(states=["A", "B", "C"])

    @state.transition(source="A", target="B")
    def transition1(self):
        pass

    @state.transition(source="B", target="C")
    def transition2(self):
        pass

    @state.transition(source="A", target="C")
    def transition3(self):
        pass


class Test(TestCase):
    def test_chart(self):
        output = fsm.chart(TestFlow.state)
        expected_output = """digraph {
"A" [label="A"];
"B" [label="B"];
"C" [label="C"];
"A" -> "B" [label="Transition1"];
"A" -> "C" [label="Transition3"];
"B" -> "C" [label="Transition2"];
}"""
        self.assertEqual(output.strip(), expected_output.strip())


class NoTargetFlow:
    # A "self-transition" that runs a side-effecting function without
    # changing state -- target is left at its DEFAULT sentinel, not None.
    state = fsm.State(states=["A", "B"])

    @state.transition(source="A", target="B")
    def advance(self):
        pass

    @state.transition(source="A")
    def touch(self):
        pass


class TestNoTargetTransition(TestCase):
    def test_no_target_transition_does_not_draw_a_default_vertex(self):
        # BUG: chart() tested `transition.target is None`, but the runtime's
        # actual "no target / unchanged" sentinel is the DEFAULT marker, not
        # None. A transition left with no explicit target (the DEFAULT
        # marker) was therefore drawn as a real "DEFAULT" vertex/edge.
        output = fsm.chart(NoTargetFlow.state)

        self.assertNotIn("DEFAULT", output)
        self.assertIn('"A" [label="A"];', output)
        self.assertIn('"B" [label="B"];', output)
        self.assertIn('"A" -> "B" [label="Advance"];', output)

    def test_explicit_none_target_is_rejected(self):
        # The runtime treats an explicit `target=None` as "set state to
        # None" (state.set(instance, None) runs, since None is not the
        # DEFAULT sentinel), while chart() used to silently drop it as if
        # it were "no target". That disagreement is exactly what produced
        # the DEFAULT-vertex bug above. `target=None` is ambiguous with
        # "no target" (the DEFAULT sentinel) is spelled by simply omitting
        # `target`, so reject the explicit None outright.
        state = fsm.State(states=["A", "B"])

        with self.assertRaises(ValueError):

            class _Flow:
                state.transition(source="A", target=None)(lambda self: None)


class Stage(Enum):
    NEW = "new"
    PUBLISHED = "published"
    REMOVED = "removed"


class EnumFlow:
    state = fsm.State(Stage, default=Stage.NEW)

    @state.transition(source=Stage.NEW, target=Stage.PUBLISHED)
    def publish(self):
        pass

    # Same source/target as publish: forces the edge sort to compare two
    # Transition objects.
    @state.transition(source=Stage.NEW, target=Stage.PUBLISHED)
    def republish(self):
        pass

    # State.ANY marker as the source.
    @state.transition(source=State.ANY, target=Stage.REMOVED)
    def remove(self):
        pass


class TestEnumChart(TestCase):
    def test_chart_with_enum_states_and_any_marker(self):
        # Regression for #476: Enum members and State.ANY markers are not
        # orderable, so sorting vertices/edges must not rely on their __lt__.
        output = fsm.chart(EnumFlow.state)
        self.assertIn("digraph {", output)
        self.assertIn('label="Publish"', output)
        self.assertIn('label="Republish"', output)
        self.assertIn("removed", output)
