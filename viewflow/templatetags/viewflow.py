from django import template
from django.template.base import Node, TemplateSyntaxError, kwarg_re


register = template.Library()


class FlowURLNode(Node):
    def __init__(self, actionname, kwargs):
        pass


@register.tag
def flowurl(parser, token):
    """
    Returns an absolute URL matching given flow action with its parameters.

    {% flowurl 'app_label/FlowCls.start' name1=value1 name2=value2 %}
    """
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one , argument"
                                  " (path to a flow action)" % bits[0])

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
