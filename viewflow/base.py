"""
Flow definition
"""
from collections import defaultdict

from django.apps import apps
from django.conf.urls import patterns

from viewflow import flow
from viewflow.urls import node_url, node_url_reverse
from viewflow.resolve import Resolver


this = flow.This()


class FlowMeta(object):
    """
    Flow options
    """
    def __init__(self, app_label, nodes):
        self.app_label = app_label
        self._nodes_by_name = nodes

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
    def __new__(cls, name, bases, attrs):
        new_class = super(FlowMetaClass, cls).__new__(cls, name, bases, attrs)

        # singleton instance
        new_class.instance = FlowInstanceDescriptor()

        # set up flow tasks
        nodes = {name: attr for name, attr in attrs.items() if isinstance(attr, flow._Node)}

        for name, node in nodes.items():
            node.name = name

        resolver = Resolver(nodes)
        for node in nodes.values():
            resolver.resolve_children_links(node)

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
        new_class._meta = FlowMeta(app_config.label, nodes)

        # flow back reference
        for name, node in nodes.items():
            node.flow_cls = new_class

        return new_class


class Flow(object, metaclass=FlowMetaClass):
    """
    Base class for flow definition
    """
    @property
    def urls(self):
        node_urls = []
        for node in self._meta.nodes():
            url_getter = getattr(self, 'url_{}'.format(node.name), None)
            url = url_getter() if url_getter else node_url(node)
            if url:
                node_urls.append(url)

        return patterns('', *node_urls)

    def reverse(self, task, **kwargs):
        reverse_impl = getattr(self, 'reverse_{}'.format(task.flow_task.name), None)
        return reverse_impl(task, **kwargs) if reverse_impl else node_url_reverse(self.urls, task, **kwargs)
