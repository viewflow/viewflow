# -*- coding: utf-8 -*-
"""
Drawing graphviz bpmn-like workflow diagrams
"""

from singledispatch import singledispatch
from viewflow import flow


def _nodename(flow_node):
    """
    Creates graphviz node name
    """
    return flow_node.name.title().replace('_', '')


def _nodelabel(flow_node):
    """
    Add line breaks between words in  node desctiption
    leaves 3 letters word on the same line
    """
    result = []

    just_added = False
    for word in flow_node.desctiption.split(' '):
        if len(result) != 0 and len(word) <= 3 and not just_added:
            result[len(result)-1] = ('%s %s' % (result[len(result)-1], word)).strip()
            just_added = True
        else:
            just_added = False
            result.append(word)
    return '\n'.join(result)


@singledispatch
def graphviz_node(flow_node):
    """
    Creates graphviz node string representation
    """
    raise NotImplementedError


@singledispatch
def graphviz_outedges(flow_node):
    """
    Creates graphviz edges representation ougining from flow_node
    """
    raise NotImplementedError


@graphviz_node.register(flow.Start)
def _(flow_node):
    return 'Start [label="", shape=circle, width="0.3", color=green, style=filled];'


@graphviz_outedges.register(flow.Start)  # NOQA
def _(flow_node):
    edges = []
    for target in flow_node.__activate_next:
        edges.append("Start -> %s" % _nodename(target.name))


@graphviz_node.register(flow.End)  # NOQA
def _(flow_node):
    return 'End [label="", shape=circle, width="0.3", color=red, style=filled];'


@graphviz_outedges.register(flow.End)  # NOQA
def _(flow_node):
    return ''


@graphviz_node.register(flow.Timer)  # NOQA
def _(flow_node):
    return '%s [shape="circle",width="0.3",height="0.3",label="⌚",fontsize=14,margin=0]' \
        % _nodename(flow_node)


@graphviz_outedges.register(flow.Timer)  # NOQA
def _(flow_node):
    edges = []
    for target in flow_node.__activate_next:
        edges.append("%s -> %s" % (_nodename(flow_node.name), _nodename(target.name)))
    return '\n'.join(edges)


@graphviz_node.register(flow.Mailbox)  # NOQA
def _(flow_node):
    return '%s [shape="circle",width="0.3",height="0.3",label="✉",fontsize=14,margin=0]' \
        % _nodename(flow_node)


@graphviz_outedges.register(flow.Mailbox)  # NOQA
def _(flow_node):
    edges = []
    for target in flow_node.__activate_next:
        edges.append("%s -> %s" % (_nodename(flow_node.name), _nodename(target.name)))
    return '\n'.join(edges)


@graphviz_node.register(flow.View)  # NOQA
def _(flow_node):
    return '%s [label="%s"]' \
        % (_nodename(flow_node), _nodelabel(flow_node.description))


@graphviz_outedges.register(flow.View)  # NOQA
def _(flow_node):
    edges = []
    for target in flow_node.__activate_next:
        edges.append("%s -> %s" % (_nodename(flow_node.name), _nodename(target.name)))
    return '\n'.join(edges)


@graphviz_node.register(flow.Job)  # NOQA
def _(flow_node):
    return '%s [label="%s"]' \
        % (_nodename(flow_node), _nodelabel(flow_node.description))


@graphviz_outedges.register(flow.Job)  # NOQA
def _(flow_node):
    edges = []
    for target in flow_node.__activate_next:
        edges.append("%s -> %s" % (_nodename(flow_node.name), _nodename(target.name)))
    return '\n'.join(edges)


@graphviz_node.register(flow.If)  # NOQA
def _(flow_node):
    return '%s [label="", shape=diamond, style=solid, width="0.3", height="0.3"]' \
        % _nodename(flow_node)


@graphviz_outedges.register(flow.If)  # NOQA
def _(flow_node):
    edges = []
    if flow_node.__on_true:
        edges.append("%s -> %s" % (_nodename(flow_node.name), _nodename(flow_node.__on_true.name)))
    if flow_node.__on_false:
        edges.append("%s -> %s" % (_nodename(flow_node.name), _nodename(flow_node.__on_false.name)))
    return '\n'.join(edges)


@graphviz_node.register(flow.Switch)  # NOQA
def _(flow_node):
    return '%s [label="", shape=diamond, style=solid, width="0.3", height="0.3"]' \
        % _nodename(flow_node)


@graphviz_outedges.register(flow.Switch)  # NOQA
def _(flow_node):
    edges = []
    for target, _ in flow_node.__activate_next:
        edges.append("%s -> %s" % (_nodename(flow_node.name), _nodename(target.name)))
    return '\n'.join(edges)


@graphviz_node.register(flow.Join)  # NOQA
def _(flow_node):
    label = "✚" if flow_node.__wait_all else ""
    return '%s [label="%s", shape=diamond, style=solid, width="0.3", height="0.3"]' \
        % (_nodename(flow_node), label)


@graphviz_outedges.register(flow.Join)  # NOQA
def _(flow_node):
    edges = []
    for target in flow_node.__activate_next:
        edges.append("%s -> %s" % (_nodename(flow_node.name), _nodename(target.name)))
    return '\n'.join(edges)


@graphviz_node.register(flow.Split)  # NOQA
def _(flow_node):
    return '%s [label="✚", shape=diamond, style=solid, width="0.3", height="0.3"]' \
        % _nodename(flow_node)


@graphviz_outedges.register(flow.Split)  # NOQA
def _(flow_node):
    edges = []
    for target, _ in flow_node.__activate_next:
        edges.append("%s -> %s" % (_nodename(flow_node.name), _nodename(target.name)))
    return '\n'.join(edges)


@graphviz_node.register(flow.First)  # NOQA
def _(flow_node):
    return '%s [label="✚", shape=diamond, style=solid, width="0.3", height="0.3"]' \
        % _nodename(flow_node)


@graphviz_outedges.register(flow.First)  # NOQA
def _(flow_node):
    edges = []
    for target in flow_node.__activate_next:
        edges.append("%s -> %s" % (_nodename(flow_node.name), _nodename(target.name)))
    return '\n'.join(edges)


def diagram(flow):
    pass
