"""
Flow definition
"""
import re
from collections import defaultdict

from django.apps import apps
from django.conf.urls import patterns

from . import flow, lock, models, forms
from .flow.base import ThisObject
from .urls import node_url, node_url_reverse


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
        app_config = apps.get_containing_app_config(module)
        subpath = module.lstrip(app_config.module.__package__+'.flows.')
        return subpath.lower().rstrip('flow').replace('.', '/')

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
        app_config = apps.get_containing_app_config(new_class.__module__)

        if app_config is None:
            raise ImportError("Flow can't be imported before app setup")
        new_class._meta = FlowMeta(app_config.label, new_class, nodes)

        # flow back reference
        for name, node in nodes.items():
            node.flow_cls = new_class

        # description
        if new_class.__doc__:
            docstring = new_class.__doc__.split('\n\n', maxsplit=1)
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
        if 'view' not in process_options.default_permissions:
            process_options.default_permissions += ('view', )

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

    @property
    def urls(self):
        """
        Provides ready to include urlpatterns required for this flow
        """
        node_urls = [
        ]

        for node in self._meta.nodes():
            url_getter = getattr(self, 'url_{}'.format(node.name), None)
            url = url_getter() if url_getter else node_url(node)

            if isinstance(url, (list, tuple)):
                node_urls += url
            elif url:
                node_urls.append(url)

        return patterns('', *node_urls), 'viewflow', self._meta.namespace

    def reverse(self, task, **kwargs):
        reverse_impl = getattr(self, 'reverse_{}'.format(task.flow_task.name), None)
        return reverse_impl(task, **kwargs) if reverse_impl else node_url_reverse(task.flow_task, task, **kwargs)

    def __str__(self):
        return self.process_title
