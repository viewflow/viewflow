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
