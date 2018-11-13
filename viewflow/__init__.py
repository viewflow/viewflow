from .activation import STATUS


default_app_config = 'viewflow.apps.ViewflowConfig'


class ThisObject(object):
    """Helper for forward references on flow tasks."""

    def __init__(self, name):  # noqa D102
        self.name = name

    @property
    def owner(self):
        """Return user that was assigned to the task."""
        def get_task_owner(activation):
            flow_class = activation.process.flow_class
            task_node = flow_class._meta.node(self.name)
            task = flow_class.task_class.objects.order_by('-id').filter(
                process=activation.process,
                flow_task=task_node,
                status=STATUS.DONE).first()
            return task.owner
        return get_task_owner


class This(object):
    """Helper for building forward referenced flow task.

    The rationale is ability to specify references to the class
    attributes and methods before they are declared.

    `this` is like a `self` but for the class body.

    The references are resolved by the metaclass at the end of the
    flow construction.

    Example::

        class MyFlow(Flow):
            start = (
                flow.StartFunction(this.start_flow)
                .Next(this.task)
            )

            task = (
                flow.View(MyView)
                .Assign(this.start.owner)
                .Next(this.end)
            )

            end = flow.End()

            def start_flow(self, activation):
                activation.prepare()
                activation.done()

    """

    def __getattr__(self, name):
        return ThisObject(name)


class Edge(object):
    """Edge of the Flow graph."""

    __slots__ = ('_src', '_dst', '_edge_class', '_label')

    def __init__(self, src, dst, edge_class):  # noqa D102
        self._src = src
        self._dst = dst
        self._edge_class = edge_class

    @property
    def src(self):
        """Edge source node."""
        return self._src

    @property
    def dst(self):
        """Edge destination node."""
        return self._dst

    @property
    def edge_class(self):
        """Type of the edge.

        Viewflow uses `next`, 'cond_true', `cond_false` and `default`
        edge classes.

        Edge class could be used as a hint for edge visualization.
        """
        return self._edge_class

    def __str__(self):
        return "[{}] {} ---> {}".format(
            self._edge_class, self._src, self._dst)


class Node(object):
    """
    Base class for flow task.

    :keyword task_type: Human readable task type
    :keyword activation_class: Activation implementation specific for this node
    """

    task_type = None
    activation_class = None

    def __init__(self, activation_class=None, **kwargs):  # noqa D102
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

        Subclasses could perform additional initialization here.
        """

    def urls(self):
        """List of urls for flow node views."""
        return []

    def get_task_url(self, task, url_type, **kwargs):
        """Return url for the task."""

    def activate(self, prev_activation, token):
        """Create task activation."""
        return self.activation_class.activate(self, prev_activation, token)


class Event(Node):
    """Base class for event-based tasks."""


class Task(Node):
    """Base class for tasks."""


class Gateway(Node):
    """Base class for task gateways."""
