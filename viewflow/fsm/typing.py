# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

from typing import Callable, Any, List, Union, Mapping, TypeVar, TYPE_CHECKING
from viewflow.this_object import ThisObject

if TYPE_CHECKING:
    from .base import TransitionMethod, Transition  # NOQA

#: The flow class a predicate is registered on. Left free so a typed
#: predicate (e.g. ``Callable[[Publication], bool]``) flows through to
#: ``state.transition(conditions=...)`` without losing its parameter type.
T = TypeVar("T")

UserModel = Any
StateValue = Any
#: ``Callable[[T], bool]`` rather than ``[object]``: under PEP 484 parameter
#: contravariance, ``[object]`` rejects narrower predicates at the registration
#: site. A free ``TypeVar`` accepts any concrete-param predicate while still
#: enforcing that all conditions in one list share a compatible instance type
#: (which a bare ``Any`` would silently drop). Runtime behavior is unchanged --
#: predicates are still invoked with the flow instance.
Condition = Union[ThisObject, Callable[[T], bool]]
Permission = Union[ThisObject, Callable[[T, Any], bool]]
StateTransitions = Mapping["TransitionMethod", List["Transition"]]
TransitionFunction = Callable[..., Any]
