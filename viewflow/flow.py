"""
Ubiquitos language for flow construction
"""
from datetime import datetime
from viewflow import activation
from viewflow.exceptions import FlowRuntimeError
from viewflow.forms import ActivationDataForm
from viewflow.models import Task, Activation


class This(object):
    """
    Helper for building forward referencied flow task
    """
    def __getattr__(self, name):
        return name


class _Edge(object):
    __slots__ = ('_src', '_dst', '_edge_class', '_label')

    def __init__(self, src, dst, edge_class, label=None):
        self._src = src
        self._dst = dst
        self._edge_class = edge_class
        self._label = label

    @property
    def src(self):
        return self._src

    @property
    def dst(self):
        return self._dst

    @property
    def edge_class(self):
        return self._edge_class

    @property
    def label(self):
        return self._label

    def __str__(self):
        edge = "[%s] %s ---> %s" % (self._edge_class, self._src, self._dst)
        if self._label:
            edge += " (%s)" % self._label
        return edge


class _Node(object):
    """
    Base class for flow objects
    """
    def __init__(self):
        self._role = None
        self._incoming_edges = []
        self.flow_cls = None
        self.name = None

    def Role(self, role):
        self._role = role
        return self

    def _outgoing(self):
        """
        Outgoing edge iterator
        """
        raise NotImplementedError

    def _incoming(self):
        """
        Incoming edge iterator
        """
        return iter(self._incoming_edges)

    def __str__(self):
        if self.name:
            return self.name.title().replace('_', ' ')
        return super(_Node, self).__str__()

    def has_perm(self, request, activation):
        raise NotImplementedError


class _Event(_Node):
    """
    Base class for event-based tasks
    """


class Start(_Node):
    """
    Start process event
    """
    task_type = 'START'
    activation_cls = activation.StartActivation

    def __init__(self, view=None):
        super(Start, self).__init__()
        self._view = view
        self._activate_next = []

    def _outgoing(self):
        for next_node in self._activate_next:
            yield _Edge(src=self, dst=next_node, edge_class='next')

    @property
    def view(self):
        from viewflow.views import start
        return self._view if self._view else start

    def Activate(self, node):
        self._activate_next.append(node)
        return self

    def start(self, data=None):
        activation = self.activation_cls(self, data)
        activation.start()
        return activation

    def done(self, activation):
        activation.done()

        # Activate all outgoing edges
        for outgoing in self._outgoing():
            outgoing.dst.activate(activation)


class End(_Node):
    """
    End process event
    """
    task_type = 'END'

    def __init__(self, view=None):
        super(End, self).__init__()
        self._view = view

    @property
    def view(self):
        from viewflow.views import end
        return self._view if self._view else end

    def _outgoing(self):
        return iter([])

    def activate(self, prev_activation):
        activation = Activation(
            process=prev_activation.process,
            started=datetime.now(),
            finished=datetime.now(),
            flow_task=self)
        activation.save()
        activation.previous.add(prev_activation)
        activation.process.finished = datetime.now()
        activation.process.save()

        # TODO Cancel all active tasks


class Timer(_Event):
    """
    Timer activated event task
    """
    task_type = 'TIMER'

    def __init__(self, minutes=None, hours=None, days=None):
        super(Timer, self).__init__()
        self._activate_next = []

    def _outgoing(self):
        for next_node in self._activate_next:
            yield _Edge(src=self, dst=next_node, edge_class='next')

    def Next(self, node):
        self._activate_next.append(node)
        return self


class Mailbox(_Event):
    """
    Message activated task
    """
    task_type = 'MAILBOX'

    def __init__(self, on_receive):
        super(Mailbox, self).__init__()
        self._activate_next = []
        self._on_receive = on_receive

    def _outgoing(self):
        for next_node in self._activate_next:
            yield _Edge(src=self, dst=next_node, edge_class='next')

    def Next(self, node):
        self._activate_next.append(node)
        return self


class _Task(_Node):
    """
    Base class for algoritmically performed tasks
    """
    def activate(self, prev_activation):
        activation = Activation(
            process=prev_activation.process,
            flow_task=self)
        activation.save()
        activation.previous.add(prev_activation)
        return activation


class View(_Task):
    """
    Human performed task
    """
    task_type = 'HUMAN'

    def __init__(self, view=None, description=None):
        super(View, self).__init__()
        self._view = view
        self._activate_next = []
        self._description = description

    @property
    def description(self):
        if self._description:
            return self.description
        return self.name.replace('_', ' ').capitalize()

    @property
    def view(self):
        from viewflow.views import task
        return self._view if self._view else task

    def _outgoing(self):
        for next_node in self._activate_next:
            yield _Edge(src=self, dst=next_node, edge_class='next')

    def Next(self, node):
        self._activate_next.append(node)
        return self

    def start(self, activation_id, data=None):
        form = ActivationDataForm(data=data, initial={'started': datetime.now()})

        if data and not form.is_valid():
            raise FlowRuntimeError('Activation metadata is broken {}'.format(form.errors))

        activation = Activation.objects.get(pk=activation_id)
        activation.form = form
        return activation

    def done(self, activation):
        # Finish activation
        activation.finished = datetime.now()
        activation.save()

        # Activate all outgoing edges
        for outgoing in self._outgoing():
            outgoing.dst.activate(activation)


class Job(_Task):
    """
    Automatically running task
    """
    task_type = 'JOB'

    def __init__(self, job):
        super(Job, self).__init__()
        self._activate_next = []
        self._job = job

    def _outgoing(self):
        for next_node in self._activate_next:
            yield _Edge(src=self, dst=next_node, edge_class='next')

    def Next(self, node):
        self._activate_next.append(node)
        return self

    def activate(self, prev_activation):
        activation = super(Job, self).activate(prev_activation)
        self._job(activation.pk)

    def start(self, activation_id):
        activation = Activation.objects.get(pk=activation_id)
        activation.started = datetime.now()
        return activation

    def done(self, activation):
        # Finish activation
        activation.finished = datetime.now()
        activation.save()

        # Activate all outgoing edges
        for outgoing in self._outgoing():
            outgoing.dst.activate(activation)


class _Gate(_Node):
    """
    Base class for flow control gates
    """


class If(_Gate):
    """
    Activates one of paths based on condition
    """
    task_type = 'IF'

    def __init__(self, cond):
        super(If, self).__init__()
        self._condition = cond
        self._on_true = None
        self._on_false = None

    def _outgoing(self):
        yield _Edge(src=self, dst=self._on_true, edge_class='cond_true')
        yield _Edge(src=self, dst=self._on_false, edge_class='cond_false')

    def OnTrue(self, node):
        self._on_true = node
        return self

    def OnFalse(self, node):
        self._on_false = node
        return self

    def activate(self, prev_activation):
        activation = Activation(
            process=prev_activation.process,
            flow_task=self)
        activation.started = datetime.now()
        activation.save()
        activation.previous.add(prev_activation)

        cond_result = self._condition(activation)

        activation.finished = datetime.now()
        activation.save()

        if cond_result:
            self._on_true.activate(activation)
        else:
            self._on_false.activate(activation)

        return activation


class Switch(_Gate):
    """
    Activates first path with matched condition
    """
    task_type = 'SWITCH'

    def __init__(self):
        super(Switch, self).__init__()
        self._activate_next = []

    def _outgoing(self):
        for next_node, cond in self._activate_next:
            edge_class = 'cond_true' if cond else 'default'
            yield _Edge(src=self, dst=next_node, edge_class=edge_class)

    def Case(self, node, cond=None):
        self._activate_next.append((node, cond))
        return self

    def Default(self, node):
        self._activate_next.append((node, None))
        return self

    def activate(self, prev_activation):
        activation = Activation(
            process=prev_activation.process,
            flow_task=self)
        activation.started = datetime.now()
        activation.save()
        activation.previous.add(prev_activation)

        next_task = None
        for node, cond in self._activate_next:
            if cond:
                if cond():
                    next_task = node
                    break
            else:
                next_task = node

        activation.finished = datetime.now()
        activation.save()

        if next_task:
            next_task.activate(activation)
        else:
            raise FlowRuntimeError('Switch have no positive condition')

        return activation


class Join(_Gate):
    """
    Wait for one or all incoming links and activate next path
    """
    task_type = 'JOIN'

    def __init__(self, wait_all=False):
        super(Join, self).__init__()
        self._wait_all = wait_all
        self._activate_next = []

    def _outgoing(self):
        for next_node in self._activate_next:
            yield _Edge(src=self, dst=next_node, edge_class='next')

    def Next(self, node):
        self._activate_next.append(node)
        return self

    def activate(self, prev_activation):
        started = datetime.now()

        # lookup for active join instance
        activations = Activation.objects.filter(
            flow_task=self,
            process=prev_activation.process,
            finished__isnull=True)

        if len(activations) > 1:
            raise FlowRuntimeError('More than one join instance for process found')

        activation = activations.first()
        if activation:
            activation.previous.add(prev_activation)
        else:
            activation = Activation(
                process=prev_activation.process,
                flow_task=self)
            activation.started = started
            activation.save()
            activation.previous.add(prev_activation)

        # check are we done
        finished_links = set(task.flow_task for task in activation.previous.all())
        all_links = set(x.src for x in self._incoming())
        if finished_links == all_links:
            activation.finished = datetime.now()
            activation.save()

            for outgoing in self._outgoing():
                outgoing.dst.activate(activation)

        return activation


class Split(_Gate):
    """
    Activate outgoing path in-parallel depends on per-path condition
    """
    task_type = 'SPLIT'

    def __init__(self):
        super(Split, self).__init__()
        self._activate_next = []

    def _outgoing(self):
        for next_node, cond in self._activate_next:
            edge_class = 'cond_true' if cond else 'default'
            yield _Edge(src=self, dst=next_node, edge_class=edge_class)

    def Next(self, node, cond=None):
        self._activate_next.append((node, cond))
        return self

    def Always(self, node):
        self._activate_next.append((node, None))
        return self

    def activate(self, prev_activation):
        activation = Activation(
            process=prev_activation.process,
            flow_task=self)
        activation.started = datetime.now()
        activation.save()
        activation.previous.add(prev_activation)

        next_tasks = []
        for node, cond in self._activate_next:
            if cond:
                if cond(activation):
                    next_tasks.append(node)
            else:
                next_tasks.append(node)

        activation.finished = datetime.now()
        activation.save()

        if next_tasks:
            for next_task in next_tasks:
                next_task.activate(activation)
        else:
            raise FlowRuntimeError('No active tasks after split')

        return activation


class First(_Gate):
    """
    Wait for first of outgoing task to be completed and cancells all others
    """
    task_type = 'FIRST_OF'

    def __init__(self):
        super(First, self).__init__()
        self._activate_list = []

    def _outgoing(self):
        for next_node in self._activate_next:
            yield _Edge(src=self, dst=next_node, edge_class='next')

    def Of(self, node):
        self._activate_list.append(node)
        return self

    def activate(self, prev_activation):
        pass  # TODO
