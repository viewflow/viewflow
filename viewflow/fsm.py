from __future__ import unicode_literals

import inspect


class TransitionNotAllowed(Exception):
    """Raised when a transition is not allowed."""


class Transition(object):
    """Allowed state change."""

    __slots__ = ('source', 'target', 'conditions')

    def __init__(self, source, target, conditions):  # noqa D102
        self.source = source
        self.target = target
        self.conditions = conditions if conditions else []

    def conditions_met(self, instance):
        """Check that all associated conditions is True."""
        return all(map(lambda condition: condition(instance), self.conditions))


class TransitionMethod(object):
    """Instance method wrapper that performs the transition."""

    do_not_call_in_templates = True

    def __init__(self, descriptor, instance):  # noqa D102
        self.descriptor = descriptor
        self.instance = instance

    def can_proceed(self, check_conditions=True):
        """Check is transition available."""
        return self.descriptor.can_proceed(self.instance, check_conditions=check_conditions)

    def original(self, *args, **kwargs):
        """Call the unwrapped class method."""
        return self.descriptor.func(self.instance, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        """Perform the transition."""
        return self.descriptor(self.instance, *args, **kwargs)


class TransitionDescriptor(object):
    """Base transition definition descriptor."""

    do_not_call_in_templates = True

    def __init__(self, state, func):  # noqa D102
        self.state = state
        self.func = func
        self.__doc__ = func.__doc__
        self.transitions = {}  # source -> transition

    @property
    def name(self):
        """Transition name."""
        return self.func.__name__

    def get_descriptor(self, instance):
        """Return a descriptor with transitions definitions.

        In this case it is `self`. The super class descriptor
        would lookup and return this object.
        """
        return self

    def add_transition(self, transition):
        """Register a new transition."""
        self.transitions[transition.source] = transition

    def get_transitions(self, instance):
        """List of all transitions."""
        return self.transitions

    def get_transition(self, source_state, instance=None):
        """Get a transition of a source_state.

        Returns None if there is no outgoing transitions.
        """
        transition = self.transitions.get(source_state, None)
        if transition is None:
            transition = self.transitions.get('*', None)
        return transition

    def can_proceed(self, instance, check_conditions=True):
        """Check is transition available."""
        current_state = self.state.get(instance)
        transition = self.get_transition(current_state, instance)
        if transition:
            return transition.conditions_met(instance)
        return False

    def __call__(self, instance, *args, **kwargs):
        """Perform the transition."""
        current_state = self.state.get(instance)
        transition = self.get_transition(current_state, instance)

        if transition is None:
            raise TransitionNotAllowed('No transition from {0}'.format(current_state))

        if not transition.conditions_met(instance):
            raise TransitionNotAllowed("Transition conditions have not been met for method '{0}'".format(self.name))

        if transition.target:
            self.state.set(instance, transition.target)

        try:
            result = self.func(instance, *args, **kwargs)
        except:
            self.state.set(instance, transition.source)
            raise
        else:
            return result

    def __get__(self, instance, type=None):
        return TransitionMethod(self, instance) if instance else self


class SuperTransitionDescriptor(TransitionDescriptor):
    """Descriptor that performs the transition described in the base class."""

    def get_descriptor(self, instance):
        """Lookup for the transition descriptor in the base classes."""
        for cls in instance.__class__.__mro__:
            if hasattr(cls, self.name):
                super_descriptor = getattr(cls, self.name)
                if not isinstance(super_descriptor, SuperTransitionDescriptor):
                    break
        else:
            raise ValueError('Base transition not found for {}'.format(self.name))

        return super_descriptor

    def get_transition(self, source_state, instance):
        """Get transition from the base class."""
        descriptor = self.get_descriptor(instance)
        return descriptor.get_transition(source_state, instance)

    def get_transitions(self, instance):
        """List of all transitions from the base class."""
        descriptor = self.get_descriptor(instance)
        return descriptor.transitions

    def can_proceed(self, instance, check_conditions=True):
        """Check is transition available."""
        descriptor = self.get_descriptor(instance)
        return descriptor.can_proceed(instance, check_conditions=check_conditions)

    def __call__(self, instance, *args, **kwargs):
        """Perform the transition."""
        descriptor = self.get_descriptor(instance)
        current_state = self.state.get(instance)
        transition = descriptor.get_transition(current_state, instance)

        if transition is None:
            raise TransitionNotAllowed('No transition from {0}'.format(current_state))

        if not transition.conditions_met(instance):
            raise TransitionNotAllowed("Transition conditions have not been met for method '{0}'".format(self.name))

        if transition.target:
            self.state.set(instance, transition.target)

        try:
            result = self.func(instance, *args, **kwargs)
        except:
            self.state.set(instance, transition.source)
            raise
        else:
            return result


class State(object):
    """A descriptor that handles state."""

    def __init__(self, default=None):  # noqa D102
        self._default = default
        self._setter = None
        self._getter = None

    def __get__(self, instance, type=None):
        if instance is None:
            return self
        return self.get(instance)

    def __set__(self, instance, value):
        if instance is None:
            raise ValueError
        self.set(instance, value)

    def get(self, instance):
        """Get the state from the underline class instance."""
        if self._getter:
            return self._getter(instance)
        return getattr(instance, self.propname, self._default)

    def set(self, instance, value):
        """Get the state of the underline class instance."""
        if self._setter:
            self._setter(instance, value)
        else:
            setattr(instance, self.propname, value)

    @property
    def propname(self):
        """Default class attribute name to store the state."""
        return '_fsm{}'.format(id(self))

    def transition(self, source=None, target=None, conditions=None):
        """Decorator to mark transition methods."""
        def _wrapper(func):
            transition_wrapper = getattr(func, '_transition', None)
            if transition_wrapper is None:
                transition_wrapper = TransitionDescriptor(self, func)
                func._transition = transition_wrapper

            source_list = source
            if not isinstance(source, (list, tuple)):
                source_list = [source]

            for src in source_list:
                field_transition = Transition(source=src, target=target, conditions=conditions)
                transition_wrapper.add_transition(field_transition)

            return transition_wrapper
        return _wrapper

    def super(self):
        """Decorator to perform the same transition as in the base class."""
        def _wrapper(func):
            transition_wrapper = SuperTransitionDescriptor(self, func)
            func._transition = transition_wrapper
            return transition_wrapper
        return _wrapper

    def setter(self):
        """Decorator to mark a way to set a state from a custom storage."""
        def _wrapper(func):
            self._setter = func
            return func
        return _wrapper

    def getter(self):
        """Decorator to mark a way to get a state from a custom storage."""
        def _wrapper(func):
            self._getter = func
            return func
        return _wrapper

    def get_available_transitions(self, instance):
        """List of transitions available from the current state."""
        transitions_cache = instance.__class__.__dict__.get('_transitions{}'.format(self.propname), None)
        if transitions_cache is None:
            transitions_cache = {}
            descriptors = inspect.getmembers(instance.__class__, lambda attr: isinstance(attr, TransitionDescriptor))
            for method_name, descriptor in descriptors:
                for source, transition in descriptor.get_transitions(instance).items():
                    if source not in transitions_cache:
                        transitions_cache[source] = []
                    transitions_cache[source].append(descriptor)

            setattr(instance.__class__, '_transitions{}'.format(self.propname), transitions_cache)

        result = [descriptor for descriptor in transitions_cache.get(self.get(instance), [])
                  if descriptor.can_proceed(instance)]
        result += [descriptor for descriptor in transitions_cache.get('*', [])
                   if descriptor.can_proceed(instance)]
        return result
