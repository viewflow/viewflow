from typing import Callable, Any, List, Mapping, TYPE_CHECKING

if TYPE_CHECKING:
    from .base import TransitionMethod, Transition  # NOQA

StateValue = Any
Condition = Callable[[Any], bool]
StateTransitions = Mapping['TransitionMethod', List['Transition']]
