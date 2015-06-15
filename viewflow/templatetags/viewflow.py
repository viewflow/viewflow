from inspect import getargspec

from django import template
from django.contrib.admin.templatetags.admin_modify import submit_row
from django.core.urlresolvers import reverse
from django.template.base import TemplateSyntaxError, TagHelperNode, parse_bits
from django.template.loader import select_template
from django.utils.module_loading import import_by_path
from django_fsm import can_proceed

from ..base import Flow
from ..compat import get_app_package
from ..models import AbstractProcess, AbstractTask
from .base import get_model_display_data


register = template.Library()


@register.tag
def flowurl(parser, token):
    """
        Returns flow url::

            {% flowurl ref [urlname] [user=]  [as varname]%}

        Usage examples::

           {% flowurl 'app_label/FlowCls' 'viewflow:index' %}
           {% flowurl flow_cls 'index' as index_url %}
           {% flowurl process 'index' %}
           {% flowurl process 'details' %}
           {% flowurl task 'assign' user=request.user %}
           {% flowurl task user=request.user %}
    """
    def geturl(ref, url_name=None, user=None):
        if isinstance(ref, Flow):
            url_ref = '{}:{}'.format(ref.namespace, url_name if url_name else 'index')
            return reverse(url_ref)
        elif isinstance(ref, AbstractProcess):
            kwargs, url_ref = {}, '{}:{}'.format(ref.flow_cls.instance.namespace, url_name if url_name else 'index')
            if url_name in ['details', 'cancel']:
                kwargs['process_pk'] = ref.pk
            return reverse(url_ref, kwargs=kwargs)
        elif isinstance(ref, AbstractTask):
            return ref.flow_task.get_task_url(ref, url_type=url_name if url_name else 'guess', user=user)
        else:
            try:
                app_label, flow_cls_path = ref.split('/')
            except ValueError:
                raise TemplateSyntaxError(
                    "Flow reference string should  looks like 'app_label/FlowCls' but '{}'".format(ref))

            app_package = get_app_package(app_label)
            if app_package is None:
                raise TemplateSyntaxError("{} app not found".format(app_label))

            flow_cls = import_by_path('{}.flows.{}'.format(app_package, flow_cls_path))
            url_ref = '{}:{}'.format(flow_cls.instance.namespace, url_name if url_name else 'index')
            return reverse(url_ref)

    class URLNode(TagHelperNode):
        def __init__(self, args, kwargs, target_var):
            super(URLNode, self).__init__(takes_context=False, args=args, kwargs=kwargs)
            self.target_var = target_var

        def render(self, context):
            resolved_args, resolved_kwargs = self.get_resolved_arguments(context)
            url = geturl(*resolved_args, **resolved_kwargs)
            if self.target_var:
                context[self.target_var] = url
                return ''
            else:
                return url

    bits = token.split_contents()[1:]

    target_var = None
    if bits[-2] == 'as':
        target_var = bits[-1]
        bits = bits[:-2]

    params, varargs, varkw, defaults = getargspec(geturl)
    args, kwargs = parse_bits(
        parser, bits, params, varargs, varkw, defaults,
        takes_context=False, name='flowurl')
    return URLNode(args, kwargs, target_var)


@register.assignment_tag
def flow_perms(user, task):
    """
    Assigns list of permissions

    {% flow_perms request.user task as task_perms  %}
    """
    result = []

    if can_proceed(task.prepare) and hasattr(task.flow_task, 'can_execute') and task.flow_task.can_execute(user, task):
        result.append('can_execute')
    elif can_proceed(task.assign) and hasattr(task.flow_task, 'can_assign') and task.flow_task.can_assign(user, task):
        result.append('can_assign')
    elif hasattr(task.flow_task, 'can_view') and task.flow_task.can_view(user, task):
        result.append('can_view')

    return result


@register.simple_tag(takes_context=True)
def include_process_data(context, process):
    """
    Shortcut tag for list all data from linked process models
    """
    opts = process.flow_cls._meta

    template_names = (
        '{}/{}/process_data.html'.format(opts.app_label, opts.flow_label),
        'viewflow/flow/process_data.html')
    template = select_template(template_names)

    context.push()
    try:
        context['process_data'] = get_model_display_data(process, context['request'].user)
        context['process'] = process
        return template.render(context)
    finally:
        context.pop()


@register.inclusion_tag('admin/viewflow/task/submit_line.html', takes_context=True)
def viewflow_task_submit_row(context):
    task = context.get('original', None)
    activation = task.activate()
    activation_cls = activation.__class__

    transitions = [(transition.name.replace('_', ' ').capitalize(), transition.name)
                   for transition in activation_cls.status.get_available_transtions(activation)]

    row_context = submit_row(context)
    row_context['transitions'] = transitions
    return row_context
