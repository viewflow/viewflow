from unittest import TestCase
from viewflow import fsm


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
