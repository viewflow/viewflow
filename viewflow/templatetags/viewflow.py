import re

from django import template
from django.apps import apps
from django.core.urlresolvers import reverse
from django.template.base import Node, TemplateSyntaxError
from django.utils.module_loading import import_by_path

from ..base import Flow


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

        if isinstance(flow_path, Flow):
            flow_cls = flow_path
        else:
            try:
                app_label, flow_cls_path = flow_path.split('/')
            except ValueError:
                raise TemplateSyntaxError("Flow action should looks like app_label/FlowCls")

            app_config = apps.get_app_config(app_label)
            if app_config is None:
                raise TemplateSyntaxError("{} app not found".format(app_label))

            if app_config.module.__package__ is not None:
                subpath = app_config.module.__package__
            else:
                subpath = app_config.module.__name__
            flow_cls = import_by_path('{}.flows.{}'.format(subpath, flow_cls_path))

        # resolve url name and args
        url = self.url_name.resolve(context)
        kwargs = {key: value.resolve(context) for key, value in self.kwargs.items()}

        return reverse(url, current_app=flow_cls._meta.namespace, kwargs=kwargs)


@register.tag
def flowurl(parser, token):
    """
    Bound to flow {% url %} tag.

    Accepts flow namespace or flow class as first argument,
    and rest same as url tag Returns an absolute URL matching
    given flow action

    Examples:

        {% flowurl flow_cls 'viewflow:index' %}
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
