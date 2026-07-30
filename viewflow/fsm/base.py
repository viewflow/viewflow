"""Base FSM declarations."""

# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

from __future__ import annotations

import inspect
from typing import Any, Dict, Mapping, Iterable, List, Optional, Tuple, Type, TypeVar
from viewflow.this_object import ThisObject
from viewflow.utils import DEFAULT, MARKER
from .typing import (
    UserModel,
    Condition,
    StateTransitions,
    Permission,
    StateValue,
    TransitionFunction,
)

#: Bound from the predicates passed to ``State.transition`` so typed
#: conditions/permissions keep their parameter type at the registration site.
T = TypeVar("T")


class TransitionNotAllowed(Exception):
    """Exception raised when a state transition is not permitted.

    Base class for :class:`NoTransition` and :class:`TransitionConditionsUnmet`.
    Catch this to handle any transition failure, or catch a subclass to
    distinguish why the transition was refused.
    """


class NoTransition(TransitionNotAllowed):
    """Raised when the current state has no transition registered for the call.

    :ivar label: human-readable label of the transition method that was called.
    :ivar state: the state the instance was in when the call was made.
    """

    def __init__(self, label: str, state: StateValue):
        self.label = label
        self.state = state
        super().__init__(f'{label} :: no transition from "{state}"')


class TransitionConditionsUnmet(TransitionNotAllowed):
    """Raised when a transition's ``conditions`` callback returned false.

    :ivar transition: the :class:`Transition` that was attempted.
    :ivar failed_condition: the first condition callable that returned false.
    :ivar unmet_message: human-readable reason from a ``State.CONDITION``
        result, or ``""`` if the condition just returned a falsy value.
    """

    def __init__(
        self,
        transition: "Transition",
        failed_condition: Condition,
        unmet_message: str = "",
    ):
        self.transition = transition
        self.failed_condition = failed_condition
        self.unmet_message = unmet_message

        condition_name = getattr(failed_condition, "__name__", repr(failed_condition))
        message = f"'{transition.label}' transition conditions have not been met: {condition_name}"
        if unmet_message:
            message = f"{message} ({unmet_message})"
        super().__init__(message)


class InvalidTargetState(TransitionNotAllowed):
    """Raised when a ``State.RETURN_VALUE``/``State.GET_STATE`` target resolves
    to a state outside its declared allowed states.

    :ivar transition: the :class:`Transition` that was attempted.
    :ivar target: the resolved (invalid) state value.
    :ivar allowed_states: the declared allowed states.
    """

    def __init__(
        self,
        transition: "Transition",
        target: StateValue,
        allowed_states: Iterable[StateValue],
    ):
        self.transition = transition
        self.target = target
        self.allowed_states = allowed_states
        super().__init__(
            f"'{transition.label}' resolved to {target!r}, which is not in the"
            f" allowed target states {list(allowed_states)!r}"
        )


class Transition:
    """
    Represents a state transition with associated conditions and permissions.
    """

    def __init__(
        self,
        func: TransitionFunction,
        source: StateValue,
        target: Optional[StateValue] = DEFAULT,
        label: Optional[str] = None,
        conditions: Optional[List[Condition]] = None,
        permission: Optional[Permission] = DEFAULT,
        custom: Optional[Dict] = None,
    ):  # noqa D102
        self.func = func
        self.source = source
        self.target = target
        self._label = label
        self.permission = permission
        self.conditions = conditions if conditions else []
        self.custom = custom if custom is not None else {}

    def __repr__(self) -> str:
        return f"<Transition({self.label} {self.source} -> {self.target}) object at {id(self)}>"

    def __str__(self) -> str:
        return f"{self.label} Transition"

    def __lt__(self, other) -> bool:
        return self.label < other.label

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
        """Checks if all conditions are met for this transition."""
        return self.get_unmet_condition(instance) is None

    def get_unmet_condition(self, instance: object) -> Optional[Tuple[Condition, Any]]:
        """Return the first ``(condition, result)`` pair that fails, or ``None``.

        Conditions are evaluated in declaration order and short-circuit on
        the first falsy result, same as :meth:`conditions_met`.
        """
        conditions = [
            (
                condition.resolve(instance.__class__)
                if isinstance(condition, ThisObject)
                else condition
            )
            for condition in self.conditions
        ]
        for condition in conditions:
            result = condition(instance)
            if not result:
                return condition, result
        return None

    def resolve_precall_target(
        self, instance: object, args: Any, kwargs: Any
    ) -> StateValue:
        """Resolve the target before the transition method runs.

        Returns ``self.target`` unchanged for a plain target or ``DEFAULT``.
        For a ``State.GET_STATE`` target, calls its function and validates
        the result against its declared ``states`` (if any). A
        ``State.RETURN_VALUE`` target isn't resolvable here -- it is only
        known after the method returns; see :meth:`resolve_return_value_target`.
        """
        target = self.target
        if isinstance(target, State.GET_STATE):
            resolved = target.func(instance, *args, **kwargs)
            self._check_allowed(resolved, target.states)
            return resolved
        return target

    def resolve_return_value_target(self, result: Any) -> StateValue:
        """Resolve a ``State.RETURN_VALUE`` target from the method's return value."""
        target = self.target
        assert isinstance(target, State.RETURN_VALUE)
        self._check_allowed(result, target.allowed_states)
        return result

    def _check_allowed(
        self, value: StateValue, allowed_states: Iterable[StateValue]
    ) -> None:
        if allowed_states and value not in allowed_states:
            raise InvalidTargetState(self, value, allowed_states)

    def declared_targets(self) -> List[StateValue]:
        """Concrete states this transition can be known to lead to ahead of a call.

        A plain (or ``DEFAULT``) target is a single-element list. A
        ``State.RETURN_VALUE``/``State.GET_STATE`` target contributes its
        declared allowed states, or an empty list if left unrestricted --
        its real target is only known once resolved at call time.
        """
        target = self.target
        if isinstance(target, State.RETURN_VALUE):
            return list(target.allowed_states)
        if isinstance(target, State.GET_STATE):
            return list(target.states)
        return [target]

    def has_perm(self, instance: object, user: UserModel) -> bool:
        """Checks if the given user has permission to perform this transition."""
        if self.permission is DEFAULT:
            return False  # Protected by default
        if self.permission is None:
            return True  # Explicitly allowed to any
        elif callable(self.permission):
            return self.permission(instance, user)
        elif isinstance(self.permission, ThisObject):
            permission = self.permission.resolve(instance)
            return permission(user)  # type: ignore
        else:
            raise ValueError(f"Unknown permission type {type(self.permission)}")


class TransitionMethod:
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


class TransitionBoundMethod:
    """Instance method wrapper that performs the transition."""

    do_not_call_in_templates = True

    class Wrapper:
        """Stateful helper driving one transition call, to simplify __call__ debug.

        A ``State.RETURN_VALUE`` target can only be resolved from the
        transition method's return value, so unlike a plain or
        ``State.GET_STATE`` target -- both resolved and applied up front in
        :meth:`begin` -- it is applied in :meth:`commit`, after the method
        has run.
        """

        def __init__(
            self,
            parent: "TransitionBoundMethod",
            args: Any,
            kwargs: Mapping[str, Any],
        ):
            self.parent = parent
            self.caller_args = args
            self.caller_kwargs = kwargs
            self.initial_state: StateValue
            self.target_state: StateValue
            self.transition: Transition

        def begin(self) -> None:
            self.initial_state = self.parent._state.get(self.parent._instance)
            transition = self.parent._descriptor.get_transition(self.initial_state)

            if transition is None:
                raise NoTransition(self.parent.label, self.initial_state)

            unmet = transition.get_unmet_condition(self.parent._instance)
            if unmet is not None:
                failed_condition, result = unmet
                unmet_message = getattr(result, "message", "")
                raise TransitionConditionsUnmet(
                    transition, failed_condition, unmet_message
                )

            self.transition = transition
            if isinstance(transition.target, State.RETURN_VALUE):
                self.target_state = DEFAULT
            else:
                self.target_state = transition.resolve_precall_target(
                    self.parent._instance, self.caller_args, self.caller_kwargs
                )
                if self.target_state is not DEFAULT:
                    self.parent._state.set(self.parent._instance, self.target_state)

        def abort(self) -> None:
            self.parent._state.set(self.parent._instance, self.initial_state)

        def commit(self, result: Any) -> None:
            if isinstance(self.transition.target, State.RETURN_VALUE):
                self.target_state = self.transition.resolve_return_value_target(result)
                if self.target_state is not DEFAULT:
                    self.parent._state.set(self.parent._instance, self.target_state)

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
        if transition:
            return (
                transition.conditions_met(self._instance) if check_conditions else True
            )
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
        wrapper = TransitionBoundMethod.Wrapper(self, args, kwargs)
        wrapper.begin()
        try:
            result = self._func(self._instance, *args, **kwargs)
        except BaseException:
            wrapper.abort()
            raise
        else:
            wrapper.commit(result)
            return result

    def get_transitions(self) -> Iterable[Transition]:
        return self._descriptor.get_transitions()


class TransitionDescriptor:
    """Base transition definition descriptor."""

    do_not_call_in_templates = True

    def __init__(self, state: StateValue, func: TransitionFunction):  # noqa D102
        self._state = state
        self._func = func
        self._transitions: Dict[StateValue, Transition] = {}

    def __get__(
        self, instance: object, owner: Optional[Type[object]] = None
    ) -> TransitionMethod | TransitionBoundMethod:
        if instance is not None:
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


class SuperTransitionDescriptor:
    do_not_call_in_templates = True

    def __init__(self, state: State, func: TransitionFunction):  # noqa D102
        self._state = state
        self._func = func

    def __get__(
        self, instance: object, owner: Optional[Type[object]] = None
    ) -> TransitionBoundMethod | TransitionMethod:
        if instance is not None:
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


class StateDescriptor:
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
            or (
                transition.source == State.ANY
                and state not in transition.declared_targets()
            )
        ]

    def get_available_transitions(self, flow, state: State, user):
        return [
            transition
            for transition in self.get_outgoing_transitions(state)
            if transition.conditions_met(flow)
            if transition.has_perm(flow, user)
        ]


class State:
    """State slot field."""

    ANY = MARKER("ANY")

    def __init__(self, states: Any, default: StateValue = None):
        self._default = default
        self._setter = None
        self._getter = None
        self._on_success = None
        self._name: Optional[str] = None

    def __set_name__(self, owner: Type[object], name: str) -> None:
        self._name = name

    def __get__(self, instance: object, owner: Optional[Type[object]] = None) -> Any:
        if instance is not None:
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
                return self._default if value is None or value == "" else value
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
        return "__fsm_{}".format(self._name)

    def transition(
        self,
        source: StateValue,
        target: Optional[StateValue] = DEFAULT,
        label: Optional[str] = None,
        conditions: Optional[List[Condition[T]]] = None,
        permission: Optional[Permission[T]] = DEFAULT,
        custom: Optional[Dict] = None,
    ) -> Any:
        """Decorator to mark a method as a state transition."""
        if target is None:
            raise ValueError(
                "target=None is ambiguous with 'no target'. Omit the target"
                " argument entirely for a transition that doesn't change state."
            )

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
                    custom=custom,
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

    class CONDITION:
        """Boolean-like object to return value accompanied with a message from fsm conditions."""

        def __init__(self, is_true: bool, unmet: str = ""):
            self.is_true = is_true
            self.unmet = unmet

        @property
        def message(self) -> str:
            return self.unmet if not self.is_true else ""

        def __bool__(self) -> bool:
            return self.is_true

    class RETURN_VALUE:
        """``target=State.RETURN_VALUE(*allowed_states)`` -- the transition
        target is the method's own return value, resolved only after it
        successfully returns (side effects in the method body already
        happened by then; there's no way to know the target any sooner).

        ``allowed_states``, if given, restricts and documents the possible
        targets: :func:`~viewflow.fsm.chart` draws an edge for each, and a
        return value outside the set raises :class:`InvalidTargetState`
        instead of silently landing on an undeclared state. Omit it to allow
        any return value.
        """

        def __init__(self, *allowed_states: StateValue):
            self.allowed_states = allowed_states

        def __repr__(self) -> str:
            return f"RETURN_VALUE{self.allowed_states!r}"

    class GET_STATE:
        """``target=State.GET_STATE(func, states=[...])`` -- the transition
        target is computed by ``func(instance, *args, **kwargs)`` from the
        call's own arguments, resolved *before* the transition method runs
        -- so, unlike ``State.RETURN_VALUE``, the method body already
        observes the new state, and nothing runs if the computed target
        turns out invalid.

        ``states``, if given, restricts and documents the possible targets:
        :func:`~viewflow.fsm.chart` draws an edge for each, and a computed
        target outside the set raises :class:`InvalidTargetState`. Omit it
        to allow any target ``func`` returns.
        """

        def __init__(
            self,
            func: TransitionFunction,
            states: Optional[List[StateValue]] = None,
        ):
            self.func = func
            self.states = states if states is not None else []

        def __repr__(self) -> str:
            name = getattr(self.func, "__name__", repr(self.func))
            return f"GET_STATE({name})"
