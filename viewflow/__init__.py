from collections import defaultdict
from viewflow import flow
from viewflow.resolve import Resolver


class FlowMeta(object):
    """
    Flow options
    """
    def __init__(self, meta, nodes):
        self._meta = meta
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


class FlowMetaClass(type):
    def __new__(cls, name, bases, attrs):
        new_class = super(FlowMetaClass, cls).__new__(cls, name, bases, attrs)

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
        meta = getattr(new_class, 'Meta', None)
        new_class._meta = FlowMeta(meta, nodes)

        return new_class


class Flow(object, metaclass=FlowMetaClass):
    """
    Base class for flow definition
    """
