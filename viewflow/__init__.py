from .activation import STATUS


class ThisObject(object):

    """Helper for forward references on flow tasks."""

    def __init__(self, name):
        self.name = name

    @property
    def owner(self):
        """Return same process finished task owner."""
        def get_task_owner(activation):
            flow_class = activation.process.flow_class
            task_node = flow_class._meta.node(self.name)
            task = flow_class.task_class.objects.get(
                process=activation.process,
                flow_task=task_node,
                status=STATUS.DONE)
            return task.owner
        return get_task_owner


class This(object):
    """Helper for building forward referenced flow task."""
    def __getattr__(self, name):
        return ThisObject(name)


class Edge(object):
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


class Node(object):
    """
    Base class for flow task.

    :keyword task_type: Human readable task type
    :keyword activation_class: Activation implementation specific for this node
    """
    task_type = None
    activation_class = None

    def __init__(self, activation_class=None, **kwargs):
        self._incoming_edges = []

        self.flow_class = None
        self.name = None

        if activation_class:
            self.activation_class = activation_class

        super(Node, self).__init__(**kwargs)

    def _outgoing(self):
        """Outgoing edge iterator."""
        raise NotImplementedError

    def _incoming(self):
        """Incoming edge iterator."""
        return iter(self._incoming_edges)

    def _resolve(self, resolver):
        """Resolve and store outgoing links."""

    def __str__(self):
        if self.name:
            return self.name.title().replace('_', ' ')
        return super(Node, self).__str__()

    def ready(self):
        """
        Called when flow class setup finished.

        Subclasses could perform additional initialisation here.
        """

    def urls(self):
        """List of urls for flow node views."""
        return []

    def get_task_url(self, task, url_type, **kwargs):
        """Return url for the task."""

    def activate(self, prev_activation, token):
        """Creates task activation."""
        return self.activation_class.activate(self, prev_activation, token)


class Event(Node):

    """Base class for event-based tasks."""


class Task(Node):

    """Base class for tasks."""


class Gateway(Node):
    """
    Base class for task gateways
    """
