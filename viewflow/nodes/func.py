from django.utils.decorators import method_decorator

from .. import Event, ThisObject, mixins
from ..activation import FuncActivation, StartActivation
from ..decorators import flow_start_func
from ..exceptions import FlowRuntimeError


class StartFunction(mixins.TaskDescriptionMixin,
                    mixins.NextNodeMixin,
                    mixins.DetailViewMixin,
                    mixins.UndoViewMixin,
                    mixins.CancelViewMixin,
                    mixins.PerformViewMixin,
                    Event):
    task_type = 'START'
    activation_class = StartActivation

    def __init__(self, func=None, **kwargs):
        self.func = func if func is not None else self.start_func_default
        super(StartFunction, self).__init__(**kwargs)

    @method_decorator(flow_start_func)
    def start_func_default(self, activation):
        activation.prepare()
        activation.done()
        return activation

    def ready(self):
        if isinstance(self.func, ThisObject):
            self.func = getattr(self.flow_class.instance, self.func.name)

    def run(self, *args, **kwargs):
        return self.func(self, *args, **kwargs)


class Function(mixins.TaskDescriptionMixin,
               mixins.NextNodeMixin,
               mixins.DetailViewMixin,
               mixins.UndoViewMixin,
               mixins.CancelViewMixin,
               mixins.PerformViewMixin,
               Event):

    task_type = 'FUNC'
    activation_class = FuncActivation

    def __init__(self, func, task_loader=None, **kwargs):
        self.func = func
        self.task_loader = task_loader
        super(Function, self).__init__(**kwargs)

    def ready(self):
        if isinstance(self.func, ThisObject):
            self.func = getattr(self.flow_class.instance, self.func.name)
        if isinstance(self.task_loader, ThisObject):
            self.task_loader = getattr(self.flow_class.instance, self.task_loader.name)

    def run(self, *args, **kwargs):
        if self.task_loader is None:
            if 'task' not in kwargs:
                if len(args) == 0 or not isinstance(args[0], self.flow_class.task_class):
                    raise FlowRuntimeError('Function {} should be called with task instance', self.name)
            return self.func(*args, **kwargs)
        else:
            task = self.task_loader(self, *args, **kwargs)
            return self.func(task, *args, **kwargs)
