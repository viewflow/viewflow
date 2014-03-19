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
    return url(r'^{}/$'.format(flow_node.name), flow_node.view, {'start_task': flow_node},
               name=flow_node.name)


@node_url.register(flow.View)  # NOQA
def _(flow_node):
    return url(r'^{}/(?P<act_id>\d+)/$'.format(flow_node.name), flow_node.view, {'flow_task': flow_node},
               name=flow_node.name)


@singledispatch
def node_url_reverse(flow_node, task, **kwargs):
    return None


@node_url_reverse.register(flow.Start)  # NOQA
def _(flow_node, task, **kwargs):
    return reverse('viewflow:start', current_app=flow_node.flow_cls._meta.namespace)


@node_url_reverse.register(flow.View)  # NOQA
def _(flow_node, task, **kwargs):
    pk = task.pk if task else kwargs.get('pk')
    return reverse('viewflow:{}'.format(flow_node.name), args=[pk], current_app=flow_node.flow_cls._meta.namespace)
