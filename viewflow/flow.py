"""
Ubiquitos language for flow construction
"""
from viewflow import activation
from viewflow.exceptions import FlowRuntimeError
from viewflow.models import Task


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
        activation = self.activation_cls(self)
        activation.start(data)
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
    activation_cls = activation.EndActivation

    def __init__(self):
        super(End, self).__init__()

    def _outgoing(self):
        return iter([])

    def activate(self, prev_activation):
        activation = self.activation_cls(self)
        activation.activate(prev_activation)
        activation.start()
        activation.done()

        # TODO Cancel all active tasks


class Timer(_Event):
    """
    TODO: Timer activated event task
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
    TODO: Message activated task
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
        activation = self.activation_cls(self)
        activation.activate(prev_activation)
        return activation

    def done(self, activation):
        activation.done()

        # Activate all outgoing edges
        for outgoing in self._outgoing():
            outgoing.dst.activate(activation)


class View(_Task):
    """
    Human performed task
    """
    task_type = 'HUMAN'
    activation_cls = activation.ViewActivation

    def __init__(self, view=None, description=None):
        super(View, self).__init__()
        self._view = view
        self._activate_next = []
        self._description = description
        self._owner = None
        self._owner_permission = None

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

    def Assign(self, owner=None, permission=None):
        if owner is not None and permission is not None:
            raise FlowRuntimeError('Only one of owner or permission could be specified')

        self._owner = owner
        self._owner_permission = permission

    def start(self, activation_id, data=None):
        task = Task.objects.get(pk=activation_id)
        activation = self.activation_cls(self, task=task)
        activation.start(data)
        return activation


class Job(_Task):
    """
    Automatically running task
    """
    task_type = 'JOB'
    activation_cls = activation.Activation

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

    def start(self, activation_id):
        task = Task.objects.get(pk=activation_id)
        activation = self.activation_cls(self, task=task)
        activation.start()
        return activation


class _Gate(_Node):
    """
    Base class for flow control gates
    """
    activation_cls = activation.Activation


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
        activation = self.activation_cls(self)
        activation.activate(prev_activation)

        activation.start()
        cond_result = self._condition(activation)
        activation.done()

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
        activation = self.activation_cls(self)
        activation.activate(prev_activation)

        activation.start()

        next_task = None
        for node, cond in self._activate_next:
            if cond:
                if cond():
                    next_task = node
                    break
            else:
                next_task = node

        activation.done()

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
        # lookup for active join instance
        tasks = Task.objects.filter(
            flow_task=self,
            process=prev_activation.process,
            status=Task.STATUS.STARTED)

        if len(tasks) > 1:
            raise FlowRuntimeError('More than one join instance for process found')

        task = tasks.first()
        if task:
            activation = self.activation_cls(self, task)
            activation.task.previous.add(prev_activation)
            activation.task.save()
        else:
            activation = self.activation_cls(self)
            activation.activate(prev_activation)
            activation.start()

        # check are we done
        all_links = set(x.src for x in self._incoming())
        finished_links = set(task.flow_task for task in activation.task.previous.all())
        if finished_links == all_links:
            activation.done()

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
        activation = self.activation_cls(self)
        activation.activate(prev_activation)

        activation.start()

        next_tasks = []
        for node, cond in self._activate_next:
            if cond:
                if cond(activation):
                    next_tasks.append(node)
            else:
                next_tasks.append(node)

        activation.done()

        if next_tasks:
            for next_task in next_tasks:
                next_task.activate(activation)
        else:
            raise FlowRuntimeError('No active tasks after split')

        return activation


class First(_Gate):
    """
    TODO: Wait for first of outgoing task to be completed and cancells all others
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
