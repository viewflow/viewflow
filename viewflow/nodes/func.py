from .. import base, mixins
from ..activation import FuncActivation, StartActivation


class StartFunction(mixins.TaskDescriptionMixin,
                    mixins.NextNodeMixin,
                    mixins.DetailsViewMixin,
                    mixins.UndoViewMixin,
                    mixins.CancelViewMixin,
                    mixins.PerformViewMixin,
                    base.Event):
    task_type = 'START'
    activation_cls = StartActivation

    def __init__(self, func=None, **kwargs):
        self.func = func if func is not None else self.start_func_default
        super(StartFunction, self).__init__(**kwargs)

    def start_func_default(self, activation):
        activation.prepare()
        activation.done()
        return activation

    def ready(self):
        if isinstance(self.func, base.ThisObject):
            self.func = getattr(self.flow_cls.instance, self.func.name)

    def run(self, *args, **kwargs):
        if isinstance(self.func, type) and issubclass(self.func, StartActivation):
            receiver = self.func()
            receiver.initialize(self, None)
            return receiver(*args, **kwargs)
        else:
            activation = self.activation_cls()
            activation.initialize(self, None)
            return self.func(activation, *args, **kwargs)


class Function(mixins.TaskDescriptionMixin,
               mixins.NextNodeMixin,
               mixins.DetailsViewMixin,
               mixins.UndoViewMixin,
               mixins.CancelViewMixin,
               mixins.PerformViewMixin,
               base.Event):

    task_type = 'FUNC'
    activation_cls = FuncActivation

    def __init__(self, func, **kwargs):
        self.func = func
        super(Function, self).__init__(**kwargs)

    def ready(self):
        if isinstance(self.func, base.ThisObject):
            self.func = getattr(self.flow_cls.instance, self.func.name)

    def run(self, *args, **kwargs):
        return self.func(self, *args, **kwargs)
