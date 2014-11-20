class TransitionNotAllowed(Exception):
    """Raised when a transition is not allowed"""


class Transition(object):
    __slots__ = ('source', 'target', 'conditions')

    def __init__(self, source, target, conditions):
        self.source = source
        self.target = target
        self.conditions = conditions if conditions else []

    def conditions_met(self, instance):
        return all(map(lambda condition: condition(instance), self.conditions))


class TransitionMethod(object):
    def __init__(self, descriptor, instance):
        self.descriptor = descriptor
        self.instance = instance

    def can_proceed(self, check_conditions=True):
        current_state = self.descriptor.state.get(self.instance)
        transition = self.descriptor.get_transition(current_state, self.instance)
        if transition:
            return transition.conditions_met(self.instance)
        return False

    def original(self, *args, **kwargs):
        return self.descriptor.func(self.instance, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self.descriptor(self.instance, *args, **kwargs)


class TransitionDescriptor(object):
    def __init__(self, state, func):
        self.state = state
        self.func = func
        self.transitions = {}  # source -> transition

    @property
    def name(self):
        return self.func.__name__

    def add_transition(self, transition):
        self.transitions[transition.source] = transition

    def get_transition(self, source_state, instance=None):
        transition = self.transitions.get(source_state, None)
        if transition is None:
            transition = self.transitions.get('*', None)
        return transition

    def __call__(self, instance, *args, **kwargs):
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
    def get_descriptor(self, instance):
        for cls in instance.__class__.__mro__:
            super_descriptor = getattr(cls, self.name)
            if not isinstance(super_descriptor, SuperTransitionDescriptor):
                break
        else:
            raise ValueError('Base transition not found for {}'.format(self.name))

        return super_descriptor

    def get_transition(self, source_state, instance):
        descriptor = self.get_descriptor(instance)
        return descriptor.get_transition(source_state, instance)

    def __call__(self, instance, *args, **kwargs):
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
    def __init__(self, default=None):
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
        if self._getter:
            return self._getter(instance)
        return getattr(instance, self.propname, self._default)

    def set(self, instance, value):
        if self._setter:
            self._setter(instance, value)
        else:
            setattr(instance, self.propname, value)

    @property
    def propname(self):
        return '_fsm{}'.format(id(self))

    def transition(self, source=None, target=None, conditions=None):
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
        def _wrapper(func):
            transition_wrapper = SuperTransitionDescriptor(self, func)
            func._transition = transition_wrapper
            return transition_wrapper
        return _wrapper

    def setter(self):
        def _wrapper(func):
            self._setter = func
            return func
        return _wrapper

    def getter(self):
        def _wrapper(func):
            self._getter = func
            return func
        return _wrapper
