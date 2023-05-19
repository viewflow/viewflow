# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is licensed under the Commercial license defined in file
# 'COMM_LICENSE', which is part of this source code package.

from enum import Enum
from typing import List, Set, Tuple
from django.db.models import Choices
from .base import State, StateDescriptor, Transition
from .typing import StateValue


def get_state_name(state_value):
    if isinstance(state_value, Enum):
        return str(state_value.value)
    return str(state_value)


def get_state_label(state_value):
    if isinstance(state_value, Choices):
        return state_value.label
    elif isinstance(state_value, Enum):
        return str(state_value.value)
    return str(state_value)


def chart(flow_state: StateDescriptor, exclude_guards=True):
    """
    Draws a directed graph (digraph) of the state transitions defined in the
    given `flow_state`.

    Args:
        flow_state (StateDescriptor): The state descriptor object.
        exclude_guards (bool): Whether to exclude transitions with no target state.

    Returns:
        str: A string representation of the digraph in the DOT language.

    The function uses the `flow_state` object to extract the transitions and the
    states involved. It then generates a DOT language string, which can be used
    with tools like Graphviz to produce an image of the graph.

    Note that the function ignores the `State.USE_RETURN_VALUE` and `State.SELECT`
    states for now, as these are not supported yet.
    """
    vertices: Set[StateValue] = set()
    postponed: List[Transition] = []
    edges: Set[Tuple[StateValue, StateValue, Transition]] = set()

    # prepare data
    for method, transitions in flow_state.get_transitions().items():
        for transition in transitions:
            if exclude_guards and transition.target is None:
                continue
            if transition.source == State.ANY:
                postponed.append(transition)
            else:
                # TODO: State.USE_RETURN_VALUE / State.SELECT
                vertices.add(transition.source)
                vertices.add(transition.target)
                edges.add((transition.source, transition.target, transition))

    for transition in postponed:
        vertices.add(transition.target)
        for vertex in vertices:
            if transition.source == State.ANY and vertex == transition.target:
                continue
            edges.add((vertex, transition.target, transition))

    # build chart
    vertices_definition = "\n".join(
        [
            '"%s" [label="%s"];' % (get_state_name(vertex), get_state_label(vertex))
            for vertex in sorted(vertices)
        ]
    )

    edges_definition = "\n".join(
        [
            f'"{source}" -> "{target}" [label="{transition.label}"];'
            for source, target, transition in sorted(edges)
        ]
    )

    return """digraph {
%s
%s
}""" % (
        vertices_definition,
        edges_definition,
    )
