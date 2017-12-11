from __future__ import unicode_literals

from collections import OrderedDict

from django import template
from django.core.exceptions import ImproperlyConfigured
from django.template import TemplateSyntaxError, Node
from django.template.base import kwarg_re
from django.template.loader import select_template
from django.urls import reverse
from django.utils.module_loading import import_string

from .. import flow
from ..base import Flow
from ..compat import get_app_package
from ..models import AbstractProcess, AbstractTask
from ..utils import get_flow_namespace
from .base import get_model_display_data


register = template.Library()


@register.tag
def flowurl(parser, token):
    """
    Return a flow url.

    Usage::

        {% flowurl ref [urlname] [user=]  [ns=] [ns_map=] [as varname]%}

    Examples::

        {% flowurl 'app_label/FlowCls' 'index' %}
        {% flowurl flow_class 'index' as index_url %}
        {% flowurl process 'index' %}
        {% flowurl process 'detail' %}
        {% flowurl task 'assign' user=request.user %}
        {% flowurl task user=request.user %}

    Examples to use links outside of flow views::

        {% flowurl task 'detail' ns='viewflow:helloworld' %}
        {% flowurl task 'detail' ns=request.resolver_match.namespace ns_map=view.ns_map %}

    """
    def geturl(ns, ref, url_name=None, user=None, ns_map=None):
        if isinstance(ref, Flow):
            namespace = get_flow_namespace(ref, ns, ns_map)
            url_ref = '{}:{}'.format(namespace, url_name if url_name else 'index')
            return reverse(url_ref)
        elif isinstance(ref, AbstractProcess):
            namespace = get_flow_namespace(ref.flow_class, ns, ns_map)
            kwargs, url_ref = {}, '{}:{}'.format(namespace, url_name if url_name else 'index')
            if url_name in ['detail', 'action_cancel']:
                kwargs['process_pk'] = ref.pk
            return reverse(url_ref, kwargs=kwargs)
        elif isinstance(ref, AbstractTask):
            namespace = get_flow_namespace(ref.flow_task.flow_class, ns, ns_map)
            return ref.flow_task.get_task_url(
                ref, url_type=url_name if url_name else 'guess',
                user=user, namespace=namespace)
        else:
            try:
                app_label, flow_class_path = ref.split('/')
            except ValueError:
                raise TemplateSyntaxError(
                    "Flow reference string should  looks like 'app_label/FlowCls' but '{}'".format(ref))

            app_package = get_app_package(app_label)
            if app_package is None:
                raise TemplateSyntaxError("{} app not found".format(app_label))

            flow_class = import_string('{}.flows.{}'.format(app_package, flow_class_path))
            namespace = get_flow_namespace(flow_class, ns, ns_map)
            url_ref = '{}:{}'.format(namespace, url_name if url_name else 'index')
            return reverse(url_ref)

    class URLNode(Node):
        def __init__(self, args, kwargs, target_var):
            self.args = args
            self.kwargs = kwargs
            self.target_var = target_var

        def render(self, context):
            request = context['request']  # TODO Check that request template context installed

            resolved_args = [arg.resolve(context) for arg in self.args]
            resolved_kwargs = {k: v.resolve(context) for k, v in self.kwargs.items()}

            base_namespace = resolved_kwargs.pop('ns', None)
            ns_map = resolved_kwargs.get('ns_map', None)

            if base_namespace is None and ns_map is None:
                base_namespace = request.resolver_match.namespace

            url = geturl(base_namespace, *resolved_args, **resolved_kwargs)
            if self.target_var:
                context[self.target_var] = url
                return ''
            else:
                return url

    bits = token.split_contents()[1:]

    args = []
    kwargs = {}
    target_var = None
    if bits[-2] == 'as':
        target_var = bits[-1]
        bits = bits[:-2]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to url tag")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))

    return URLNode(args, kwargs, target_var)



@register.simple_tag
def flow_perms(user, task):
    """
    Assign list of permissions.

    Example::

        {% flow_perms request.user task as task_perms  %}

    """
    result = []

    if hasattr(task.flow_task, 'can_execute') and task.flow_task.can_execute(user, task):
        result.append('can_execute')
    if hasattr(task.flow_task, 'can_assign') and task.flow_task.can_assign(user, task):
        result.append('can_assign')
    if hasattr(task.flow_task, 'can_view') and task.flow_task.can_view(user, task):
        result.append('can_view')

    return result


@register.simple_tag
def flow_start_actions(flow_class, user=None):
    """
    List of actions to start flow available for the user.

    Example::
        {% flow_start_actions view.flow_class request.user as flow_start_actions %}
    """
    actions = [
        node for node in flow_class._meta.nodes()
        if isinstance(node, flow.Start)
        if user is None or node.can_execute(user)
    ]
    return sorted(actions, key=lambda node: node.name)


@register.simple_tag
def flows_start_actions(flow_classes, user=None):
    """
    List of actions to start each flow available for the user.

    Example::

        {% flows_start_actions view.flows request.user as flow_start_actions %}
    """
    actions = OrderedDict()
    for flow_class in sorted(flow_classes, key=lambda flow_class: flow_class.process_title):
        actions[flow_class] = flow_start_actions(flow_class, user=user)
    return actions


@register.simple_tag(takes_context=True)
def include_process_data(context, process):
    """Shortcut tag for list all data from linked process models."""
    if 'request' not in context:
        raise ImproperlyConfigured(
            "include_process_data template tag requires 'django.core.context_processors.request'"
            " context processor installed.")

    opts = process.flow_class._meta

    template_names = (
        '{}/{}/process_data.html'.format(opts.app_label, opts.flow_label),
        'viewflow/flow/process_data.html')
    template = select_template(template_names)
    context.push()
    try:
        context['process_data'] = get_model_display_data(process, context['request'].user)
        context['process'] = process
        return template.render(context.flatten() if hasattr(context, 'flatten') else context)
    finally:
        context.pop()
