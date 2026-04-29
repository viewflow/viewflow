# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

from typing import Callable, Any, List, Union, Mapping, TYPE_CHECKING
from viewflow.this_object import ThisObject

if TYPE_CHECKING:
    from .base import TransitionMethod, Transition  # NOQA

UserModel = Any
StateValue = Any
# Note: Callable parameter is ``Any`` (rather than ``object``) so a typed
# predicate that takes a specific flow class — e.g.
# ``Callable[[Publication], bool]`` — type-checks under pyright/mypy at
# the registration site. With ``[object]``, parameter contravariance
# rejects narrower predicates (a function that only accepts
# ``Publication`` is *not* substitutable where ``Callable[[object], bool]``
# is expected). ``Any`` is gradually typed, so any concrete-param
# predicate flows through cleanly. Runtime behavior is unchanged —
# predicates are still invoked with the flow instance.
Condition = Union[ThisObject, Callable[[Any], bool]]
Permission = Union[ThisObject, Callable[[Any, Any], bool]]
StateTransitions = Mapping["TransitionMethod", List["Transition"]]
TransitionFunction = Callable[..., Any]
