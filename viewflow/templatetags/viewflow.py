import re

from django import template
from django.core.urlresolvers import reverse
from django.template.base import Node, TemplateSyntaxError
from django.utils.module_loading import import_by_path

from ..base import Flow
from ..compat import get_app_package


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

            app_package = get_app_package(app_label)
            if app_package is None:
                raise TemplateSyntaxError("{} app not found".format(app_label))

            flow_cls = import_by_path('{}.flows.{}'.format(app_package, flow_cls_path))

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


class FlowUserTaskUrlNode(Node):
    def __init__(self, user, task, target_var=None):
        self.user = user
        self.task = task
        self.target_var = target_var

    def render(self, context):
        user = self.user.resolve(context)
        task = self.task.resolve(context)

        url = task.flow_task.flow_cls.instance.get_user_task_url(task=task, user=user)

        if self.target_var:
            context[self.target_var] = url
            return ''
        else:
            return url


@register.tag
def flow_usertask_url(parser, token):
    """
    {% flow_usertask_url request.user task 'execute' %}
    {% flow_usertask_url request.user task 'execute' as task_url %}
    """
    bits = token.split_contents()

    if len(bits) < 3 or bits[-2] != 'as':
        raise TemplateSyntaxError("'{}' takes at least two arguments (user task)".format(bits[0]))

    task = parser.compile_filter(bits[1])
    user = parser.compile_filter(bits[2])
    target_var = bits[-1]

    return FlowUserTaskUrlNode(user, task, target_var)


@register.assignment_tag
def flow_perms(user, task):
    """
    Assigns list of permissions

    {% flow_perms request.user task as task_perms  %}
    """
    result = []

    if hasattr(task.flow_task, 'can_execute') and task.flow_task.can_execute(user, task):
        result.append('can_execute')
    elif hasattr(task.flow_task, 'can_assign') and task.flow_task.can_assign(user, task):
        result.append('can_assign')
    elif hasattr(task.flow_task, 'can_view') and task.flow_task.can_view(user, task):
        result.append('can_view')

    return result
