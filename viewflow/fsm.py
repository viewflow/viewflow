from functools import partial


class TransitionNotAllowed(Exception):
    """Raised when a transition is not allowed"""


class Transition(object):
    __slots__ = ('source', 'target', 'on_error', 'conditions')

    def __init__(self, source, target, on_error, conditions):
        self.source = source
        self.target = target
        self.on_error = on_error
        self.conditions = conditions if conditions else []

    def conditions_met(self, instance):
        return all(map(lambda condition: condition(instance), self.conditions))


class TransitionMethodProxy(object):
    def __init__(self, transition_method, instance):
        self.transition_method = transition_method
        self.instance = instance

    def __call__(self, *args, **kwargs):
        return self.transition_method(self.instance, *args, **kwargs)

    def __getattr__(self, name):
        if name == 'original':
            return partial(self.transition_method.func, self.instance)
        elif name == 'can_proceed':
            return partial(self.transition_method.can_proceed, self.instance)
        return getattr(self.transition_method, name)


class TransitionMethod(object):
    def __init__(self, state, func):
        self.state = state
        self.func = func
        self.transitions = {}  # source -> transition

    @property
    def name(self):
        return self.func.__name__

    def can_proceed(self, instance, check_conditions=True):
        current_state = self.state.get(instance)
        transition = self.get_transition(current_state)
        if transition:
            return transition.conditions_met(instance)
        return False

    def add_transition(self, transition):
        self.transitions[transition.source] = transition

    def get_transition(self, source_state):
        transition = self.transitions.get(source_state, None)
        if transition is None:
            transition = self.transitions.get('*', None)
        return transition

    def __call__(self, instance, *args, **kwargs):
        current_state = self.state.get(instance)
        transition = self.get_transition(current_state)

        if transition is None:
            raise TransitionNotAllowed('No transition from {0}'.format(current_state))

        if not transition.conditions_met(instance):
            raise TransitionNotAllowed("Transition conditions have not been met for method '{0}'".format(self.name))

        result = self.func(instance, *args, **kwargs)

        if transition.target:
            self.state.set(instance, transition.target)

        return result

    def __get__(self, instance, type=None):
            if instance:
                return TransitionMethodProxy(self, instance)
            else:
                return self


class SuperTransitionMethod(TransitionMethod):
    def __call__(self, instance, *args, **kwargs):
        current_state = self.state.get(instance)
        super_wrapper = getattr(super(instance.__class__, instance), self.name)
        transition = super_wrapper.get_transition(current_state)

        if transition is None:
            raise TransitionNotAllowed('No transition from {0}'.format(current_state))

        if not transition.conditions_met(instance):
            raise TransitionNotAllowed("Transition conditions have not been met for method '{0}'".format(self.name))

        result = self.func(instance, *args, **kwargs)

        if transition.target:
            self.state.set(instance, transition.target)

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

    def transition(self, source=None, target=None, on_error=None, conditions=None):
        def _wrapper(func):
            transition_wrapper = getattr(func, '_transition', None)
            if transition_wrapper is None:
                transition_wrapper = TransitionMethod(self, func)
                func._transition = transition_wrapper

            source_list = source
            if not isinstance(source, (list, tuple)):
                source_list = [source]

            for src in source_list:
                field_transition = Transition(source=src, target=target, on_error=on_error, conditions=conditions)
                transition_wrapper.add_transition(field_transition)

            return transition_wrapper
        return _wrapper

    def super(self):
        def _wrapper(func):
            transition_wrapper = SuperTransitionMethod(self, func)
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
