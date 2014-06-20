import re
from collections import defaultdict

from django import template
from django.apps import apps
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.template.base import Node, TemplateSyntaxError
from django.utils.module_loading import import_by_path


kwarg_re = re.compile(r"(\w+)=?(.+)")
register = template.Library()


class FlowURLNode(Node):
    def __init__(self, flow_ref, url_name, kwargs):
        self.flow_ref = flow_ref
        self.url_name = url_name
        self.kwargs = kwargs

    def render(self, context):
        # resolve flow reference
        flow_path = self.flow_ref.resolve(context)

        try:
            app_label, flow_cls_path = flow_path.split('/')
        except ValueError:
            raise TemplateSyntaxError("Flow action should looks like app_label/FlowCls")

        app_config = apps.get_app_config(app_label)
        if app_config is None:
            raise TemplateSyntaxError("{} app not found".format(app_label))

        flow_cls = import_by_path('{}.flows.{}'.format(app_config.module.__package__, flow_cls_path))

        # resolve url name
        url = self.url_name.resolve(context)

        return reverse(url, current_app=flow_cls._meta.namespace, kwargs=self.kwargs)


class ViewFormNode(Node):
    def __init__(self, template, nodelist):
        self.template = template
        self.nodelist = nodelist

    def render(self, context):
        template = self.template.resolve(context)
        if not callable(getattr(template, 'render', None)):
            # If not, we'll try get_template
            template = get_template(template)

        context['_viewparts'] = defaultdict(dict)  # part_name -> part_id -> part_nodes
        for part in self.nodelist.get_nodes_by_type(ViewPartNode):
            value = part.render(context)
            part_id = part.part_id.resolve(context)
            context['_viewparts'][part.part_name][part_id] = value

        return template.render(context)


class ViewPartNode(Node):
    def __init__(self, part_name, part_id, nodelist):
        self.part_name = part_name
        self.part_id = part_id
        self.nodelist = nodelist

    def render(self, context):
        part_id = self.part_id.resolve(context)

        if part_id in context['_viewparts'][self.part_name]:
            return context['_viewparts'][self.part_name][part_id]

        for part in self.nodelist.get_nodes_by_type(ViewPartNode):
            value = part.render(context)
            part_id = part.part_id.resolve(context)

            if part_id not in context['_viewparts'][part.part_name]:
                context['_viewparts'][part.part_name][part_id] = value

        return self.nodelist.render(context)


@register.tag
def flowurl(parser, token):
    """
    Bound to flow {% url %} tag.

    Accepts flow namespace as first argument, and rest same as url tag
    Returns an absolute URL matching given flow action

    Examples:

        {% flowurl 'app_label/FlowCls' 'viewflow:index' %}
        {% flowurl 'app_label/FlowCls' 'viewflow:task_name' process_pk=1 task_pk=2 other_arg='value' %}
    """
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError("'{}' takes at least two arguments (flow namespace)".format(bits[0]))

    kwargs = {}

    flow_ref = parser.compile_filter(bits[1])
    actionname = parser.compile_filter(bits[2])

    for bit in bits[3:]:
        match = kwarg_re.match(bit)
        if not match:
            raise TemplateSyntaxError("Malformed arguments in flow_url tag {}".format(bit))

        name, value = match.groups()
        if name:
            kwargs[name] = parser.compile_filter(value)

    return FlowURLNode(flow_ref, actionname, kwargs)


@register.tag
def viewform(parser, token):
    """
    Component form render
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'{}' takes at least one argument <template_name>".format(bits[0]))

    template = parser.compile_filter(bits[1])
    nodelist = parser.parse(('endviewform',))
    parser.delete_first_token()

    return ViewFormNode(template, nodelist)


@register.tag
def viewpart(parser, token):
    """
    Redefinable part of viewform template
    """
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError("'{}' takes at least one argument <part_name> <part_id>".format(bits[0]))

    part_name = parser.compile_filter(bits[1]).token
    part_id = parser.compile_filter(bits[2])
    nodelist = parser.parse(('endviewpart',))
    parser.delete_first_token()

    return ViewPartNode(part_name, part_id, nodelist)
