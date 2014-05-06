# -*- coding: utf-8 -*-
"""
Drawing graphviz bpmn-like workflow diagrams
"""
import subprocess
from singledispatch import singledispatch
from viewflow import flow


def _nodename(flow_node):
    """
    Creates graphviz node name
    """
    return flow_node.name.title().replace('_', '')


def _nodelabel(flow_node):
    """
    Add line breaks between words in  node description
    leaves 3 letters word on the same line
    """
    result = []

    just_added = False

    for word in flow_node.description.split(' '):
        if len(result) != 0 and len(word) <= 3 and not just_added:
            result[len(result)-1] = ('%s %s' % (result[len(result)-1], word)).strip()
            just_added = True
        else:
            just_added = False
            result.append(word)
    return '\\n'.join(result)


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
    for target in flow_node._activate_next:
        edges.append("Start -> %s" % _nodename(target))
    return '\n'.join(edges)


@graphviz_node.register(flow.End)  # NOQA
def _(flow_node):
    return 'End [label="", shape=circle, width="0.3", color=red, style=filled];'


@graphviz_outedges.register(flow.End)  # NOQA
def _(flow_node):
    return ''


@graphviz_node.register(flow.View)  # NOQA
def _(flow_node):
    return '%s [label="%s"];' \
        % (_nodename(flow_node), _nodelabel(flow_node))


@graphviz_outedges.register(flow.View)  # NOQA
def _(flow_node):
    edges = []
    for target in flow_node._activate_next:
        edges.append("%s -> %s;" % (_nodename(flow_node), _nodename(target)))
    return '\n'.join(edges)


@graphviz_node.register(flow.Job)  # NOQA
def _(flow_node):
    return '%s [label="%s"];' \
        % (_nodename(flow_node), _nodelabel(flow_node))


@graphviz_outedges.register(flow.Job)  # NOQA
def _(flow_node):
    edges = []
    for target in flow_node._activate_next:
        edges.append("%s -> %s;" % (_nodename(flow_node), _nodename(target)))
    return '\n'.join(edges)


@graphviz_node.register(flow.If)  # NOQA
def _(flow_node):
    return '%s [label="", shape=diamond, style=solid, width="0.3", height="0.3"];' \
        % _nodename(flow_node)


@graphviz_outedges.register(flow.If)  # NOQA
def _(flow_node):
    edges = []
    if flow_node._on_true:
        edges.append("%s -> %s;" % (_nodename(flow_node), _nodename(flow_node._on_true)))
    if flow_node._on_false:
        edges.append("%s -> %s;" % (_nodename(flow_node), _nodename(flow_node._on_false)))
    return '\n'.join(edges)


@graphviz_node.register(flow.Switch)  # NOQA
def _(flow_node):
    return '%s [label="", shape=diamond, style=solid, width="0.3", height="0.3"];' \
        % _nodename(flow_node)


@graphviz_outedges.register(flow.Switch)  # NOQA
def _(flow_node):
    edges = []
    for target, _ in flow_node._activate_next:
        edges.append("%s -> %s;" % (_nodename(flow_node), _nodename(target)))
    return '\n'.join(edges)


@graphviz_node.register(flow.Join)  # NOQA
def _(flow_node):
    label = "✚" if flow_node._wait_all else ""
    return '%s [label="%s", shape=diamond, style=solid, width="0.3", height="0.3"];' \
        % (_nodename(flow_node), label)


@graphviz_outedges.register(flow.Join)  # NOQA
def _(flow_node):
    edges = []
    for target in flow_node._activate_next:
        edges.append("%s -> %s;" % (_nodename(flow_node), _nodename(target)))
    return '\n'.join(edges)


@graphviz_node.register(flow.Split)  # NOQA
def _(flow_node):
    return '%s [label="✚", shape=diamond, style=solid, width="0.3", height="0.3"];' \
        % _nodename(flow_node)


@graphviz_outedges.register(flow.Split)  # NOQA
def _(flow_node):
    edges = []
    for target, _ in flow_node._activate_next:
        edges.append("%s -> %s;" % (_nodename(flow_node), _nodename(target)))
    return '\n'.join(edges)


@graphviz_node.register(flow.First)  # NOQA
def _(flow_node):
    return '%s [label="✚", shape=diamond, style=solid, width="0.3", height="0.3"];' \
        % _nodename(flow_node)


@graphviz_outedges.register(flow.First)  # NOQA
def _(flow_node):
    edges = []
    for target in flow_node._activate_next:
        edges.append("%s -> %s;" % (_nodename(flow_node), _nodename(target)))
    return '\n'.join(edges)


def diagram(flow_cls, output_file_name=None):
    diagramm = """
    digraph %s {
        graph [size="10,5", rankdir=LR, splines=ortho,constraint=false ];
        node [shape=box, style=rounded, fontsize=8];
    """ % flow_cls.__name__

    for node in flow_cls._meta.nodes():
        diagramm += "    %s\n" % graphviz_node(node)

    for node in flow_cls._meta.nodes():
        diagramm += "    %s\n" % graphviz_outedges(node)

    diagramm += """
    }
    """

    if output_file_name:
        dot = subprocess.Popen(['dot', '-Tpng', '-o', output_file_name],
                               stdout=subprocess.PIPE,
                               stdin=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        dot.stdin.write(bytes(diagramm, 'UTF-8'))
        stdout, _ = dot.communicate()
        assert not stdout

    return diagramm
