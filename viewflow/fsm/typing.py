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
Condition = Union[ThisObject, Callable[[object, object], bool]]
Permission = Union[ThisObject, Callable[[object, Any], bool]]
StateTransitions = Mapping['TransitionMethod', List['Transition']]
TransitionFunction = Callable[..., Any]
