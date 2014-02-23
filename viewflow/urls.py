"""
Construction flow task urls
"""
from singledispatch import singledispatch
from django.conf.urls import url
from viewflow import flow


@singledispatch
def node_url(flow_node):
    return None


@node_url.register(flow.Start)
def _(flow_node):
    if flow_node._view:
        return url(r'^start/$', flow_node._view, {'start_task': flow_node})


@node_url.register(flow.View)  # NOQA
def _(flow_node):
    import ipdb; ipdb.set_trace()
    return url(r'^{}/(?P<act_id>\d+)/$'.format(flow_node.name), flow_node._view, {'flow_task': flow_node})


@singledispatch
def node_url_reverse(flow_node, task, **kwargs):
    return None


@node_url_reverse.register(flow.Start)  # NOQA
def _(flow_node, task, **kwargs):
    pass
