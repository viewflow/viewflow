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
    """
    Start function task to state a flow from the code.

    Example::

        class MyFlow(Flow):
           start = (
               flow.StartFunction(this.start_flow)
               .Next(this.end)
           )

           ....

           @method_decorator(flow.flow_start_func)
           def on_shipment_receive(self, activation, shipment):
                activation.prepare()
                activation.process.shipment = shipment
                activation.done()

    """

    task_type = 'START'
    activation_class = StartActivation

    def __init__(self, func=None, **kwargs):
        """
        Instantiate a StartFunction task.

        :param func: Callable[activation, **kwargs]
        """
        self.func = func if func is not None else self.start_func_default
        super(StartFunction, self).__init__(**kwargs)

    @method_decorator(flow_start_func)
    def start_func_default(self, activation):
        """Default implementation for start function.

        Do nothing, just create a new process instance.
        """
        activation.prepare()
        activation.done()
        return activation

    def ready(self):
        """Resolve internal `this`-references."""
        if isinstance(self.func, ThisObject):
            self.func = getattr(self.flow_class.instance, self.func.name)

    def run(self, *args, **kwargs):
        """Execute the function task."""
        return self.func(self, *args, **kwargs)


class Function(mixins.TaskDescriptionMixin,
               mixins.NextNodeMixin,
               mixins.DetailViewMixin,
               mixins.UndoViewMixin,
               mixins.CancelViewMixin,
               mixins.PerformViewMixin,
               Event):
    """
    Function task to be executed outside of the flow.

    Example::

        class MyFlow(Flow):
            ...

            shipment_received_handler = (
               flow.Function(
                   this.on_shipment_receive,
                   task_loader=this.get_shipment_handler_task)
               .Next(this.end)
           )

           ....

           @method_decorator(flow.flow_func)
           def on_shipment_receive(self, activation, shipment):
                activation.prepare()
                activation.done()

           def get_shipment_handler_task(self, flow_task, shipment):
                return Task.objects.get(process=shipment.process)

    Somewhere in you code::

        ...
        MyFlow.shipment_received_handler.run(shipment)

    """

    task_type = 'FUNC'
    activation_class = FuncActivation

    def __init__(self, func, task_loader=None, **kwargs):
        """
        Instantiate a Function task.

        :param func: Callable[activation, **kwargs]
        :param task_loader: Callable[**kwargs] -> Task

        `task_loader` could be a `this` reference to the class
        instance method.

        You can skip a `task_loader` if the function going to be
        called with Task instance, ex::

             class MyFlow(Flow):
                 ...

                 shipment_received_handler = (
                     flow.Function(
                         this.on_shipment_receive,
                         task_loader='')
                     .Next(this.end)
                 )

                 ...

             task = Task.objects.get(pk=request.GET['task_pk'])
             MyFlow.shipment_received_handler.run(task=task)

        """
        self.func = func
        self.task_loader = task_loader
        super(Function, self).__init__(**kwargs)

    def ready(self):
        """Resolve internal `this`-references."""
        if isinstance(self.func, ThisObject):
            self.func = getattr(self.flow_class.instance, self.func.name)
        if isinstance(self.task_loader, ThisObject):
            self.task_loader = getattr(self.flow_class.instance, self.task_loader.name)

    def run(self, *args, **kwargs):
        """Execute the function task."""
        if self.task_loader is None:
            if 'task' not in kwargs:
                if len(args) == 0 or not isinstance(args[0], self.flow_class.task_class):
                    raise FlowRuntimeError('Function {} should be called with task instance', self.name)
            return self.func(*args, **kwargs)
        else:
            task = self.task_loader(self, *args, **kwargs)
            return self.func(task, *args, **kwargs)
