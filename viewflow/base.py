"""
Flow definition
"""
import re
from collections import defaultdict
from textwrap import dedent

from django.conf.urls import include, url

from . import lock, models, forms
from .activation import STATUS
from .compat import get_containing_app_data


class ThisObject(object):

    """Helper for forward references on flow tasks."""

    def __init__(self, name):
        self.name = name

    @property
    def owner(self):
        """Return same process finished task owner."""
        def get_task_owner(activation):
            flow_cls = activation.process.flow_cls
            task_node = flow_cls._meta.node(self.name)
            task = flow_cls.task_cls.objects.get(
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
    :keyword activation_cls: Activation implementation specific for this node
    """
    task_type = None
    activation_cls = None

    def __init__(self, activation_cls=None, **kwargs):
        self._incoming_edges = []

        self.flow_cls = None
        self.name = None

        if activation_cls:
            self.activation_cls = activation_cls

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
        return self.activation_cls.activate(self, prev_activation, token)


class Event(Node):

    """Base class for event-based tasks."""


class Task(Node):

    """Base class for tasks."""


class Gateway(Node):
    """
    Base class for task gateways
    """


class _Resolver(object):
    """
    Resolver of task inter-links
    """
    def __init__(self, nodes):
        self.nodes = nodes  # map name -> node instance

    def get_implementation(self, link):
        if isinstance(link, Node):
            return link
        elif isinstance(link, ThisObject):
            node = self.nodes.get(link.name)
            if not node:
                raise ValueError("Can't found node with name %s" % link.name)
            return node
        elif isinstance(link, str):
            node = self.nodes.get(link)
            if not node:
                raise ValueError("Can't found node with name %s" % link)
            return node

        raise ValueError("Can't resolve %s" % link)


class FlowMeta(object):
    """
    Flow options
    """
    def __init__(self, app_label, flow_cls, nodes):
        self.app_label = app_label
        self.flow_cls = flow_cls
        self._nodes_by_name = nodes

    @property
    def flow_label(self):
        module = "{}.{}".format(self.flow_cls.__module__, self.flow_cls.__name__)
        app_label, app_package = get_containing_app_data(module)

        subpath = module[len(app_package) + 1:]
        if subpath.startswith('flows.'):
            subpath = subpath[len('flows.'):]
        if subpath.endswith('Flow'):
            subpath = subpath[:-len('Flow')]

        return subpath.lower().replace('.', '/')

    def nodes(self):
        """
        Nodes iterator
        """
        return self._nodes_by_name.values()

    def node(self, name):
        """
        Get node by name
        """
        return self._nodes_by_name.get(name, None)


class FlowInstanceDescriptor(object):
    def __init__(self):
        self.flow_instance = None

    def __get__(self, instance=None, owner=None):
        if self.flow_instance is None:
            self.flow_instance = owner()
        return self.flow_instance


class FlowMetaClass(type):
    def __new__(cls, class_name, bases, attrs):
        new_class = super(FlowMetaClass, cls).__new__(cls, class_name, bases, attrs)

        # singleton instance
        new_class.instance = FlowInstanceDescriptor()

        # set up flow tasks
        nodes = {name: attr for name, attr in attrs.items() if isinstance(attr, Node)}

        for name, node in nodes.items():
            node.name = name

        resolver = _Resolver(nodes)
        for node in nodes.values():
            node._resolve(resolver)

        incoming = defaultdict(lambda: [])  # node -> [incoming_nodes]
        for _, node in nodes.items():
            for outgoing_edge in node._outgoing():
                incoming[outgoing_edge.dst].append(outgoing_edge)
        for target, edges in incoming.items():
            target._incoming_edges = edges

        # set up workflow meta
        app_label, _ = get_containing_app_data(new_class.__module__)

        if app_label is None:
            get_containing_app_data(new_class.__module__)
            raise ImportError("Flow can't be imported before app setup")
        new_class._meta = FlowMeta(app_label, new_class, nodes)

        # flow back reference
        for name, node in nodes.items():
            node.flow_cls = new_class

        # description
        if new_class.__doc__:
            docstring = new_class.__doc__.split('\n\n', 1)
            if 'process_title' not in attrs and len(docstring) > 0:
                new_class.process_title = docstring[0].strip()
            if 'process_description' not in attrs and len(docstring) > 1:
                new_class.process_description = dedent(docstring[1]).strip()
        else:
            # convert camel case to separate words
            new_class.process_title = re.sub('([a-z0-9])([A-Z])', r'\1 \2',
                                             re.sub('(.)([A-Z][a-z]+)', r'\1 \2', class_name)) \
                .rstrip('Flow')

        # view process permission
        process_options = new_class.process_cls._meta
        if hasattr(process_options, 'default_permissions'):
            # django 1.7
            for permission in ('view', 'manage'):
                if permission not in process_options.default_permissions:
                    process_options.default_permissions += (permission,)
        else:
            # django 1.6
            permissions = (('view_{}'.format(process_options.model_name),
                            'View {}'.format(process_options.model_name)),
                           ('manage_{}'.format(process_options.model_name),
                            'Manage {}'.format(process_options.model_name)))

            for permission in permissions:
                if permission not in process_options.permissions:
                    process_options.permissions.append(permission)

        # done flow setup
        for name, node in nodes.items():
            node.ready()

        return new_class


class Flow(object, metaclass=FlowMetaClass):
    """
    Base class for flow definition

    :keyword process_cls: Defines model class for Process
    :keyword task_cls: Defines model class for Task
    :keyword management_form_cls: Defines form class for task state tracking over GET requests
    :keyword lock_impl: Locking implementation for flow

    """
    process_cls = models.Process
    task_cls = models.Task
    management_form_cls = forms.ActivationDataForm
    lock_impl = lock.no_lock

    process_title = None
    process_description = None

    summary_template = "{{ flow_cls.process_title }} - {{ process.status }}"

    @property
    def urls(self):
        """
        Provides ready to include urlpatterns required for this flow
        """
        node_urls = []
        for node in self._meta.nodes():
            node_urls += node.urls()

        return url('^', include(node_urls), {'flow_cls': self})

    @property
    def view_permission_name(self):
        opts = self.process_cls._meta
        return "{}.view_{}".format(opts.app_label, opts.model_name)

    @property
    def manage_permission_name(self):
        opts = self.process_cls._meta
        return "{}.manage_{}".format(opts.app_label, opts.model_name)

    def __str__(self):
        return self.process_title


this = This()
