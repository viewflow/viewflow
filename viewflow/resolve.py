"""
Resolver of task inter-links
"""
from singledispatch import singledispatch
from viewflow import flow
from viewflow.flow.base import ThisObject


@singledispatch
def node_callable(flow_node):
    """
    Callable task implementation attached to flow node
    None - if task have no attached callable
    """
    return None


@node_callable.register(flow.View)
def _(flow_node):
    return flow_node.view


@node_callable.register(flow.Job)  # NOQA
def _(flow_node):
    return flow_node._job


@singledispatch
def resolve_children_links(flow_node, resolver):
    """
    Change linked declared tasks  to task instance
    """
    raise NotImplementedError(type(flow_node))


@resolve_children_links.register(flow.Start)  # NOQA
def _(flow_node, resolver):
    flow_node._activate_next = \
        [resolver.get_implementation(node) for node in flow_node._activate_next]


@resolve_children_links.register(flow.End)  # NOQA
def _(flow_node, resolver):
    """
    No outgoing links
    """


@resolve_children_links.register(flow.View)  # NOQA
def _(flow_node, resolver):
    flow_node._activate_next = \
        [resolver.get_implementation(node) for node in flow_node._activate_next]


@resolve_children_links.register(flow.Job)  # NOQA
def _(flow_node, resolver):
    flow_node._activate_next = \
        [resolver.get_implementation(node) for node in flow_node._activate_next]


@resolve_children_links.register(flow.If)  # NOQA
def _(flow_node, resolver):
    flow_node._on_true = resolver.get_implementation(flow_node._on_true)
    flow_node._on_false = resolver.get_implementation(flow_node._on_false)


@resolve_children_links.register(flow.Switch)  # NOQA
def _(flow_node, resolver):
    flow_node._activate_next = \
        [(resolver.get_implementation(node), cond) for node, cond in flow_node._activate_next]


@resolve_children_links.register(flow.Join)  # NOQA
def _(flow_node, resolver):
    flow_node._activate_next = \
        [resolver.get_implementation(node) for node in flow_node._activate_next]


@resolve_children_links.register(flow.Split)  # NOQA
def _(flow_node, resolver):
    flow_node._activate_next = \
        [(resolver.get_implementation(node), cond) for node, cond in flow_node._activate_next]


@resolve_children_links.register(flow.First)  # NOQA
def _(flow_node, resolver):
    flow_node._activate_next = \
        [resolver.get_implementation(node) for node in flow_node._activate_list]


class Resolver(object):
    """
    Resolver of task inter-links
    """
    def __init__(self, nodes):
        self.nodes = nodes  # map name -> node instance
        self.callables = {node_callable(node): node
                          for node in self.nodes.values()
                          if node_callable(node) is not None}

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
        elif callable(link):
            node = self.callables.get(link)
            if not node:
                raise ValueError("Can't found node for callable %s" % link.__name__)
            return node

        raise ValueError("Can't resolve %s" % link)

    def resolve_children_links(self, task):
        resolve_children_links(task, self)
