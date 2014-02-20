"""
Construction flow task urls
"""
from singledispatch import singledispatch


@singledispatch
def node_url(flow_node):
    return None


@singledispatch
def node_url_reverse(flow_node):
    return None
