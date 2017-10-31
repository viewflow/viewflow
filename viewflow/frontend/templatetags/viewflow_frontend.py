from __future__ import unicode_literals

from django import template
from viewflow.models import Task

register = template.Library()


@register.filter
def url(query):
    """Helper to get an url without GET parameters."""
    if query:
        return query.split('?')[0]


@register.inclusion_tag('viewflow/includes/task_management_menu.html')
def task_management_menu(activation, request):
    """Available tasks actions."""
    actions = []
    if request.user.has_perm(activation.flow_class._meta.manage_permission_name):
        for transition in activation.get_available_transitions():
            if transition.can_proceed(activation):
                url = activation.flow_task.get_task_url(
                    activation.task, transition.name, user=request.user,
                    namespace=request.resolver_match.namespace)
                if url:
                    actions.append((transition.name.replace('_', ' ').title(), url))

    return {'actions': actions,
            'request': request}


@register.filter
def view_permission_name(flow_class):
    return flow_class._meta.view_permission_name


@register.filter
def manage_permission_name(flow_class):
    return flow_class._meta.manage_permission_name


@register.filter
def inbox_count(flows, user):
    """List of tasks assigned for the user."""
    return Task.objects.inbox(flows, user).count()


@register.filter
def queue_count(flows, user):
    """List of tasks available to assign to the user."""
    return Task.objects.queue(flows, user).count()
