"""
The viewflow.fsm module provides an implementation of finite state machine (FSM)
workflows that enables users to define and execute sequential workflows with
multiple states and transitions.
"""

# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

from .admin import FlowAdminMixin
from .base import (
    InvalidTargetState,
    NoTransition,
    Transition,
    TransitionConditionsUnmet,
    TransitionNotAllowed,
    State,
)
from .chart import chart
from .fields import FSMField, NonInitialStateOnCreate, transition
from .viewset import FlowViewsMixin


__all__ = (
    "TransitionNotAllowed",
    "NoTransition",
    "TransitionConditionsUnmet",
    "InvalidTargetState",
    "State",
    "FlowAdminMixin",
    "chart",
    "Transition",
    "FlowViewsMixin",
    "FSMField",
    "NonInitialStateOnCreate",
    "transition",
)
