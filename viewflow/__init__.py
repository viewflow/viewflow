from viewflow import flow
from viewflow.resolve import Resolver


class FlowMeta(object):
    """
    Flow options
    """
    def __init__(self, meta):
        pass


class FlowMetaClass(type):
    def __new__(cls, name, bases, attrs):
        new_class = super(FlowMetaClass, cls).__new__(cls, name, bases, attrs)

        # set up workflow meta
        meta = getattr(new_class, 'Meta', None)
        new_class._meta = FlowMeta(meta)

        # set up flow tasks
        nodes = {name: attr for name, attr in attrs.items() if isinstance(attr, flow._Node)}

        resolver = Resolver(nodes)
        for node in nodes.values():
            resolver.resolve_children_links(node)

        return new_class


class Flow(object, metaclass=FlowMetaClass):
    """
    Base class for flow definition
    """
