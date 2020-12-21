# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial licence defined in file 'COMM_LICENSE',
# which is part of this source code package.

from typing import Callable, Any, List, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from .base import TransitionMethod, Transition  # NOQA

StateValue = Any
Condition = Callable[[Any], bool]
StateTransitions = Mapping['TransitionMethod', List['Transition']]
