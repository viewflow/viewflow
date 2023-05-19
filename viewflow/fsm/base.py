"""Base FSM declarations."""

# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

from __future__ import annotations

import inspect
from typing import Any, Dict, Mapping, Iterable, List, Type, Optional
from viewflow.this_object import ThisObject
from viewflow.utils import MARKER
from .typing import (
    UserModel,
    Condition,
    StateTransitions,
    Permission,
    StateValue,
    TransitionFunction,
)


class TransitionNotAllowed(Exception):
    """Raised when a transition is not allowed."""


class Transition(object):
    """
    A state transition definition.
    """

    def __init__(
        self,
        func: TransitionFunction,
        source: StateValue,
        target: Optional[StateValue],
        label: Optional[str] = None,
        conditions: Optional[List[Condition]] = None,
        permission: Optional[Permission] = None,
    ):  # noqa D102
        self.func = func
        self.source = source
        self.target = target
        self._label = label
        self.permission = permission
        self.conditions = conditions if conditions else []

    def __repr__(self) -> str:
        return f"<Transition({self.label} {self.source} -> {self.target}) object at {id(self)}>"

    def __str__(self) -> str:
        return f"{self.label} Transition"

    @property
    def label(self) -> str:
        """Return the human-readable label for the transition."""
        if self._label:
            return self._label
        else:
            try:
                return self.func.label  # type: ignore
            except AttributeError:
                return self.func.__name__.title()

    @property
    def slug(self) -> str:
        """Return the slugified version of the transition function name."""
        return self.func.__name__

    def conditions_met(self, instance: object) -> bool:
        """Check if all associated conditions are met for the transition."""
        conditions = [
            condition.resolve(instance.__class__)
            if isinstance(condition, ThisObject)
            else condition
            for condition in self.conditions
        ]
        return all(map(lambda condition: condition(instance), conditions))

    def has_perm(self, instance: object, user: UserModel) -> bool:
        """Check if the user has the required permission to execute the transition."""
        if self.permission is None:
            return False
        elif callable(self.permission):
            return self.permission(instance, user)
        elif isinstance(self.permission, ThisObject):
            permission = self.permission.resolve(instance)
            return permission(user)  # type: ignore
        else:
            raise ValueError(f"Unknown permission type {type(self.permission)}")


class TransitionMethod(object):
    """Unbound transition method wrapper.

    Provides shortcut to enumerate all method transitions, ex::

        Review.publish.get_transitions()
    """

    do_not_call_in_templates = True

    def __init__(
        self,
        state: State,
        func: TransitionFunction,
        descriptor: TransitionDescriptor,
        owner: Type[object],
    ):
        self._state = state
        self._func = func
        self._descriptor = descriptor
        self._owner = owner

        self.__doc__ = func.__doc__

    def get_transitions(self) -> Iterable[Transition]:
        return self._descriptor.get_transitions()

    @property
    def slug(self) -> str:
        """Transition name."""
        return self._func.__name__


class TransitionBoundMethod(object):
    """Instance method wrapper that performs the transition."""

    do_not_call_in_templates = True

    class Wrapper(object):
        """Wrapper context object, to simplify __call__ method debug"""

        def __init__(self, parent: "TransitionBoundMethod", kwargs: Mapping[str, Any]):
            self.parent = parent
            self.caller_kwargs = kwargs
            self.initial_state: StateValue
            self.target_state: StateValue

        def __enter__(self) -> None:
            self.initial_state = self.parent._state.get(self.parent._instance)
            transition = self.parent._descriptor.get_transition(self.initial_state)

            if transition is None:
                raise TransitionNotAllowed(
                    f'{self.parent.label} :: no transition from "{self.initial_state}"'
                )

            if not transition.conditions_met(self.parent._instance):
                raise TransitionNotAllowed(
                    f" '{transition.label}' transition conditions have not been met"
                )

            self.target_state = transition.target
            if self.target_state:
                self.parent._state.set(self.parent._instance, self.target_state)

        def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Any,
        ) -> None:
            if exc_type is not None:
                self.parent._state.set(self.parent._instance, self.initial_state)
            else:
                self.parent._state.transition_succeed(
                    self.parent._instance,
                    self.parent,
                    self.initial_state,
                    self.target_state,
                    **self.caller_kwargs,
                )

    def __init__(
        self,
        state: State,
        func: TransitionFunction,
        descriptor: TransitionDescriptor,
        instance: object,
    ):
        self._state = state
        self._func = func
        self._descriptor = descriptor
        self._instance = instance

    def original(self, *args: Any, **kwargs: Any) -> Any:
        """Call the unwrapped class method."""
        return self._func(self._instance, *args, **kwargs)

    def can_proceed(self, check_conditions: bool = True) -> bool:
        """Check is transition available."""
        current_state = self._state.get(self._instance)
        transition = self._descriptor.get_transition(current_state)
        if transition and check_conditions:
            return transition.conditions_met(self._instance)
        return False

    def has_perm(self, user: UserModel) -> bool:
        current_state = self._state.get(self._instance)
        transition = self._descriptor.get_transition(current_state)
        if transition:
            return transition.has_perm(self._instance, user)
        return False

    @property
    def label(self) -> str:
        """Transition human-readable label."""
        current_state = self._state.get(self._instance)
        transition = self._descriptor.get_transition(current_state)
        if transition:
            return transition.label
        else:
            try:
                return self._func.label  # type: ignore
            except AttributeError:
                return self._func.__name__.title()

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        with TransitionBoundMethod.Wrapper(self, kwargs=kwargs):
            return self._func(self._instance, *args, **kwargs)

    def get_transitions(self) -> Iterable[Transition]:
        return self._descriptor.get_transitions()


class TransitionDescriptor(object):
    """Base transition definition descriptor."""

    do_not_call_in_templates = True

    def __init__(self, state: StateValue, func: TransitionFunction):  # noqa D102
        self._state = state
        self._func = func
        self._transitions: Dict[StateValue, Transition] = {}

    def __get__(
        self, instance: object, owner: Optional[Type[object]] = None
    ) -> TransitionMethod | TransitionBoundMethod:
        if instance:
            return TransitionBoundMethod(self._state, self._func, self, instance)
        else:
            assert owner is not None  # make mypy happy
            return TransitionMethod(self._state, self._func, self, owner)

    def add_transition(self, transition: Transition) -> None:
        self._transitions[transition.source] = transition

    def get_transitions(self) -> Iterable[Transition]:
        """List of all transitions."""
        return self._transitions.values()

    def get_transition(self, source_state: StateValue) -> Optional[Transition]:
        """Get a transition of a source_state.

        Returns None if there is no outgoing transitions.
        """
        transition = self._transitions.get(source_state, None)
        if transition is None:
            transition = self._transitions.get(State.ANY, None)
        return transition


class SuperTransitionDescriptor(object):
    do_not_call_in_templates = True

    def __init__(self, state: State, func: TransitionFunction):  # noqa D102
        self._state = state
        self._func = func

    def __get__(
        self, instance: object, owner: Optional[Type[object]] = None
    ) -> TransitionBoundMethod | TransitionMethod:
        if instance:
            return TransitionBoundMethod(
                self._state,
                self._func,
                self.get_descriptor(instance.__class__),
                instance,
            )
        else:
            assert owner is not None  # make mypy happy
            return TransitionMethod(
                self._state, self._func, self.get_descriptor(owner), owner
            )

    def get_descriptor(self, owner: Type[object]) -> TransitionDescriptor:
        """Lookup for the transition descriptor in the base classes."""
        for cls in owner.__mro__[1:]:
            if hasattr(cls, self._func.__name__):
                super_method = getattr(cls, self._func.__name__)
                if isinstance(super_method, TransitionMethod):
                    break
        else:
            raise ValueError("Base transition not found")

        return super_method._descriptor


class StateDescriptor(object):
    """Class-bound value for a state descriptor.

    Provides shortcut to enumerate all class transitions, ex::

        Review.state.get_transitions()
    """

    def __init__(self, state: "State", owner: type):
        self._state = state
        self._owner = owner

    def __getattr__(self, attr: str) -> Any:
        return getattr(self._state, attr)

    def get_transitions(self) -> StateTransitions:
        propname = "__fsm_{}_transitions".format(self._state.propname)
        transitions: StateTransitions = self._owner.__dict__.get(propname, None)
        if transitions is None:
            transitions = {}

            methods = inspect.getmembers(
                self._owner, lambda attr: isinstance(attr, TransitionMethod)
            )
            transitions = {method: method.get_transitions() for _, method in methods}
            setattr(self._owner, propname, transitions)

        return transitions

    def get_outgoing_transitions(self, state: State) -> List[Transition]:
        return [
            transition
            for transitions in self.get_transitions().values()
            for transition in transitions
            if transition.source == state
            or (transition.source == State.ANY and transition.target != state)
        ]

    def get_available_transitions(self, flow, state: State, user):
        return [
            transition
            for transition in self.get_outgoing_transitions(state)
            if transition.conditions_met(flow)
            if transition.has_perm(flow, user)
        ]


class State(object):
    """State slot field."""

    ANY = MARKER("ANY")

    def __init__(self, states: Any, default: StateValue = None):
        self._default = default
        self._setter = None
        self._getter = None
        self._on_success = None

    def __get__(self, instance: object, owner: Optional[Type[object]] = None) -> Any:
        if instance:
            return self.get(instance)
        assert owner is not None  # make mypy happy
        return StateDescriptor(self, owner)

    def __set__(self, instance: object, value: StateValue) -> None:
        raise AttributeError("Direct state modification is not allowed")

    def get(self, instance: object) -> Any:
        """Get the state from the underline class instance."""
        if self._getter:
            value = self._getter(instance)
            if self._default:
                return value if value else self._default
            else:
                return value
        return getattr(instance, self.propname, self._default)

    def set(self, instance: object, value: StateValue) -> None:
        """Get the state of the underline class instance."""
        if self._setter:
            self._setter(instance, value)
        else:
            setattr(instance, self.propname, value)

    def transition_succeed(
        self,
        instance: object,
        descriptor: TransitionBoundMethod,
        source: State,
        target: State,
        **kwargs: Any,
    ) -> None:
        if self._on_success:
            self._on_success(instance, descriptor, source, target, **kwargs)

    @property
    def propname(self) -> str:
        """State storage attribute."""
        return "__fsm{}".format(id(self))

    def transition(
        self,
        source: StateValue,
        target: Optional[StateValue] = None,
        label: Optional[str] = None,
        conditions: Optional[List[Condition]] = None,
        permission: Optional[Permission] = None,
    ) -> Any:
        """Transition method decorator."""

        def _wrapper(func: Any) -> Any:
            if isinstance(func, TransitionDescriptor):
                descriptor = func
            else:
                descriptor = TransitionDescriptor(self, func)

            source_list = source
            if not isinstance(source, (list, tuple, set)):
                source_list = [source]

            for src in source_list:
                transition = Transition(
                    func=descriptor._func,
                    source=src,
                    target=target,
                    label=label,
                    conditions=conditions,
                    permission=permission,
                )
                descriptor.add_transition(transition)

            return descriptor

        return _wrapper

    def super(self) -> Any:
        def _wrapper(func: Any) -> Any:
            return SuperTransitionDescriptor(self, func)

        return _wrapper

    def setter(self) -> Any:
        def _wrapper(func: Any) -> Any:
            self._setter = func
            return func

        return _wrapper

    def getter(self) -> Any:
        def _wrapper(func: Any) -> Any:
            self._getter = func
            return func

        return _wrapper

    def on_success(self) -> Any:
        def _wrapper(func: Any) -> Any:
            self._on_success = func
            return func

        return _wrapper

    class CONDITION(object):
        """Boolean-like object to return value accompanied with a message from fsm conditions."""

        def __init__(self, is_true: bool, unmet: str = ""):
            self.is_true = is_true
            self.unmet = unmet

        @property
        def message(self) -> str:
            return self.unmet if not self.is_true else ""

        def __bool__(self) -> bool:
            return self.is_true
