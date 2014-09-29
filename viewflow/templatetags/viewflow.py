from inspect import getargspec

from django import template
from django.core.urlresolvers import reverse
from django.template.base import TemplateSyntaxError, TagHelperNode, parse_bits
from django.utils.module_loading import import_by_path
from django_fsm import can_proceed

from ..base import Flow
from ..compat import get_app_package
from ..models import AbstractProcess, AbstractTask

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
            url_ref = 'viewflow:{}'.format(url_name if url_name else 'index')
            return reverse(url_ref, current_app=ref._meta.namespace)
        elif isinstance(ref, AbstractProcess):
            kwargs, url_ref = {}, 'viewflow:{}'.format(url_name if url_name else 'index')
            if url_name == 'details':
                kwargs['process_pk'] = ref.pk
            return reverse(url_ref, current_app=ref.flow_cls._meta.namespace, kwargs=kwargs)
        elif isinstance(ref, AbstractTask):
            return ref.get_absolute_url(user=user, url_type=url_name)
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
            url_ref = 'viewflow:{}'.format(url_name if url_name else 'index')
            return reverse(url_ref, current_app=flow_cls._meta.namespace)

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
