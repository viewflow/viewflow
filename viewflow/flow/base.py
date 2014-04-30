"""
Base definitions for flow task delcaration
"""


class This(object):
    """
    Helper for building forward referencied flow task
    """
    def __getattr__(self, name):
        return name


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
    Base class for flow task

    :keyword task_type: Human readable task type
    :keyword activation_cls: Activation implementation specific for this node
    """
    task_type = None
    activation_cls = None

    def __init__(self, activation_cls=None):
        self._incoming_edges = []

        self.flow_cls = None
        self.name = None
        if activation_cls:
            self.activation_cls = activation_cls

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
        return super(Node, self).__str__()

    def activate(self, prev_activation, token):
        """
        Creates task activation
        """
        return self.activation_cls.activate(self, prev_activation, token)


class Event(Node):
    """
    Base class for event-based tasks
    """


class Task(Node):
    """
    Base class for tasks
    """


class Gateway(Node):
    """
    Base class for task gateways
    """
