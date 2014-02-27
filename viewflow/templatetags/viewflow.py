import re
from django import template
from django.apps import apps
from django.template.base import Node, TemplateSyntaxError
from django.utils.module_loading import import_by_path

from viewflow.urls import node_url_reverse


kwarg_re = re.compile(r"(\w+)=?(.+)")
register = template.Library()


class FlowURLNode(Node):
    def __init__(self, actionname, kwargs):
        self.kwargs = kwargs
        self.actionname = actionname

    def render(self, context):
        flow_path = self.actionname.resolve(context)

        # resolve flow reference
        try:
            app_label, flow_path = flow_path.split('/')
            flow_cls_path, action_name = flow_path.rsplit('.', 1)
        except ValueError:
            raise TemplateSyntaxError("Flow action should looks like app_label/FlowCls.action")

        app_config = apps.get_app_config(app_label)
        if app_config is None:
            raise TemplateSyntaxError("{} app not found".format(app_label))

        flow_cls = import_by_path('{}.flows.{}'.format(app_config.module.__package__, flow_cls_path))
        flow_task = getattr(flow_cls, action_name, None)
        if not flow_task:
            raise TemplateSyntaxError("Action {} not found".format(action_name))

        # url reverse
        reverse_impl = getattr(flow_cls, 'reverse_{}'.format(flow_task.name), None)
        if reverse_impl:
            return reverse_impl(task=None, **self.kwargs)
        else:
            return node_url_reverse(flow_task, task=None, **self.kwargs)


@register.tag
def flowurl(parser, token):
    """
    Returns an absolute URL matching given flow action with its parameters.

    {% flowurl 'app_label/FlowCls.start' name1=value1 name2=value2 %}
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'{}' takes at least one , argument" " (path to a flow action)".format(bits[0]))

    kwargs = {}

    actionname = parser.compile_filter(bits[1])
    for bit in bits[2:]:
        match = kwarg_re.match(bit)
        if not match:
            raise TemplateSyntaxError("Malformed arguments to url tag")

        name, value = match.groups()
        if name:
            kwargs[name] = parser.compile_filter(value)

    return FlowURLNode(actionname, kwargs)
