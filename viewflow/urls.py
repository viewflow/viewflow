"""
Construction flow task urls
"""
from singledispatch import singledispatch

from django.core.urlresolvers import reverse
from django.conf.urls import url

from viewflow import flow


@singledispatch
def node_url(flow_node):
    return None


@node_url.register(flow.Start)
def _(flow_node):
    return url(r'^start/$', 'start', {'start_task': flow_node}, name='start')


@node_url.register(flow.View)  # NOQA
def _(flow_node):
    return url(r'^{}/(?P<act_id>\d+)/$'.format(flow_node.name), flow_node._view, {'flow_task': flow_node})


@singledispatch
def node_url_reverse(flow_node, task, **kwargs):
    return None


@node_url_reverse.register(flow.Start)  # NOQA
def _(flow_node, task, **kwargs):
    return reverse('viewflow:start', current_app=flow_node.flow_cls._meta.app_label)

#reverse('viewflow:shipment.views.fill_post_label', args=[1], current_app='shipment')
