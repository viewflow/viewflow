"""
Flow definition
"""
from __future__ import unicode_literals

import re
from collections import defaultdict
from textwrap import dedent
from six import with_metaclass

from django.conf.urls import include, url


from . import Node, ThisObject, This, lock, models, forms
from .compat import get_containing_app_data


class _Resolver(object):
    """Resolver this-references over flow nodes."""

    def __init__(self, nodes):  # noqa
        self.nodes = nodes  # map name -> node instance

    def get_implementation(self, link):
        if isinstance(link, Node):
            return link
        elif isinstance(link, ThisObject):
            node = self.nodes.get(link.name)
            if not node:
                raise ValueError("Cannot find node with name '%s'." % link.name)
            return node
        elif isinstance(link, str):
            node = self.nodes.get(link)
            if not node:
                raise ValueError("Cannot find node with name '%s'." % link)
            return node

        raise ValueError("Can't resolve %s" % link)


class FlowMeta(object):
    """Flow meta options."""

    def __init__(self, app_label, flow_class, nodes):  # noqa D102
        self.app_label = app_label
        self.flow_class = flow_class
        self._nodes_by_name = nodes

    @property
    def flow_label(self):
        """Unique flow label."""
        module = "{}.{}".format(self.flow_class.__module__, self.flow_class.__name__)
        app_label, app_package = get_containing_app_data(module)

        subpath = module[len(app_package) + 1:]
        if subpath.startswith('flows.'):
            subpath = subpath[len('flows.'):]
        if subpath.endswith('Flow'):
            subpath = subpath[:-len('Flow')]

        return subpath.lower().replace('.', '/')

    def nodes(self):
        """Iterator over all flow nodes."""
        return self._nodes_by_name.values()

    def node(self, name):
        """Return a node by name."""
        return self._nodes_by_name.get(name, None)

    @property
    def view_permission_name(self):
        """Name of the permission to view flow instances."""
        opts = self.flow_class.process_class._meta
        return "{}.view_{}".format(opts.app_label, opts.model_name)

    @property
    def manage_permission_name(self):
        """Name of the permission to administer flow instances."""
        opts = self.flow_class.process_class._meta
        return "{}.manage_{}".format(opts.app_label, opts.model_name)


class FlowInstanceDescriptor(object):
    """Singleton flow instance descriptor."""

    def __init__(self):  # noqa D102
        self.flow_instance = None

    def __get__(self, instance=None, owner=None):
        if self.flow_instance is None:
            self.flow_instance = owner()
        return self.flow_instance


class FlowMetaClass(type):
    """The metaclass for all flows.

    Instantiate a flow class singleton, and resolves all flow nodes
    interlinks.
    """

    def __new__(cls, class_name, bases, attrs):
        """Construct new flow class."""
        new_class = super(FlowMetaClass, cls).__new__(cls, class_name, bases, attrs)

        # singleton instance
        new_class.instance = FlowInstanceDescriptor()

        # set up flow tasks
        nodes = {}
        for base_class in bases:
            for name, attr in base_class.__dict__.items():
                if isinstance(attr, Node):
                    nodes[name] = attr
        nodes.update({name: attr for name, attr in attrs.items()
                      if isinstance(attr, Node)})

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
            node.flow_class = new_class

        # description
        if new_class.__doc__:
            docstring = new_class.__doc__.split('\n\n', 1)
            if 'process_title' not in attrs and len(docstring) > 0:
                new_class.process_title = docstring[0].strip()
            if 'process_description' not in attrs and len(docstring) > 1:
                new_class.process_description = dedent(docstring[1]).strip()
        else:
            if 'process_title' not in attrs:
                # convert camel case to separate words
                new_class.process_title = re.sub('([a-z0-9])([A-Z])', r'\1 \2',
                                                 re.sub('(.)([A-Z][a-z]+)', r'\1 \2', class_name))
                if new_class.process_title.endswith(' Flow'):
                    new_class.process_title = new_class.process_title[:-5]

        # view process permission
        process_options = new_class.process_class._meta
        for permission in ('view', 'manage'):
            if permission not in process_options.default_permissions:
                process_options.default_permissions += (permission,)

        # done flow setup
        for name, node in nodes.items():
            node.ready()

        return new_class


class Flow(with_metaclass(FlowMetaClass, object)):
    """
    Base class for flow definition::

        class MyFlow(Flow):
            start = flow.StartFunction().Next(this.end)
            end = flow.End()

    :keyword process_class: Defines model class for Process
    :keyword task_class: Defines model class for Task
    :keyword management_form_class: Defines form class for task state tracking over GET requests
    :keyword lock_impl: Locking implementation for flow
    :keyword instance: the singleton instance"

    """

    process_class = models.Process
    task_class = models.Task
    management_form_class = forms.ActivationDataForm
    lock_impl = lock.no_lock

    process_title = None
    process_description = None

    summary_template = "{{ flow_class.process_title }} - {{ process.status }}"

    @property
    def urls(self):
        """
        Build URL patterns list for all flow nodes::

            urlpatterns = [
                url(r'^admin/', include('admin.site.urls')),
                MyFlow.instance.urls,
            ]
        """
        node_urls = []
        for node in self._meta.nodes():
            node_urls += node.urls()

        return url('^', include(node_urls), {'flow_class': self})

    def has_view_permission(self, user):
        return user.has_perm(self._meta.view_permission_name)

    def __str__(self):
        return str(self.process_title)


this = This()
