"""
Flow definition
"""
import re
from collections import defaultdict

from django.conf.urls import include, url

from . import flow, lock, models, forms
from .compat import get_containing_app_data
from .flow.base import ThisObject

this = flow.This()


class _Resolver(object):
    """
    Resolver of task inter-links
    """
    def __init__(self, nodes):
        self.nodes = nodes  # map name -> node instance

    def get_implementation(self, link):
        if isinstance(link, flow.Node):
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
    def namespace(self):
        return "{}/{}".format(self.app_label, self.flow_label)

    @property
    def flow_label(self):
        module = "{}.{}".format(self.flow_cls.__module__, self.flow_cls.__name__)
        app_label, app_package = get_containing_app_data(module)

        subpath = module[len(app_package)+1:]
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
        nodes = {name: attr for name, attr in attrs.items() if isinstance(attr, flow.Node)}

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
                new_class.process_description = docstring[1].strip()
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
    def namespace(self):
        return "{}/{}".format(self._meta.app_label, self._meta.flow_label)

    @property
    def urls(self):
        """
        Provides ready to include urlpatterns required for this flow
        """
        node_urls = []
        for node in self._meta.nodes():
            node_urls += node.urls()

        return url('^', include(node_urls))

    @property
    def view_permission_name(self):
        opts = self.process_cls._meta
        return "{}.view_{}".format(opts.app_label, opts.model_name)

    @property
    def manage_permission_name(self):
        opts = self.process_cls._meta
        return "{}.view_{}".format(opts.app_label, opts.model_name)

    def __str__(self):
        return self.process_title
