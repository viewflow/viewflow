from __future__ import unicode_literals

from django import template
from viewflow.models import Task

try:
    from urllib.parse import quote
except:
    from urllib import quote


register = template.Library()


@register.filter
def query_back(request, back):
    """
    Sets the `back` url GET parameter

    Usage::

        <a href="{{ url }}?{{ request|query_back:"here" }}>
        <a href="{{ url }}?{{ request|query_back:"here_if_none" }}>
        <a href="{{ url }}?{{ request|query_back:"copy" }}>
    """
    if back not in ['here', 'copy', 'here_if_none']:
        raise template.TemplateSyntaxError(
            'query_back tag accepts `here`, `copy` or `here_if_none` as parameter. Got {}'.format(back))

    params = request.GET.copy()
    params.pop('_pjax', None)

    if back == 'here_if_none' and 'back' in params:
        """
        Do nothing
        """
    elif back == 'copy':
        """
        Do nothing
        """
    else:
        params.pop('back', None)
        if params:
            back = "{}?{}".format(quote(request.path), quote(params.urlencode()))
        else:
            back = "{}".format(quote(request.path))
        params['back'] = back

    return params.urlencode()


@register.filter
def url(query):
    if query:
        return query.split('?')[0]


@register.inclusion_tag('viewflow/includes/task_management_menu.html')
def task_management_menu(activation, request):
    actions = []
    if request.user.has_perm(activation.flow_class.manage_permission_name):
        for transition in activation.get_available_transtions():
            if transition.can_proceed(activation):
                url = activation.flow_task.get_task_url(
                    activation.task, transition.name, user=request.user,
                    namespace=request.resolver_match.namespace)
                if url:
                    actions.append((transition.name, url))

    return {'actions': actions,
            'request': request}


@register.filter
def inbox_count(flows, user):
    return Task.objects.inbox(flows, user).count()


@register.filter
def queue_count(flows, user):
    return Task.objects.queue(flows, user).count()
