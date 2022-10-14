from django import template
from django.template.loader import select_template

from viewflow.utils import get_object_data


register = template.Library()


@register.simple_tag(takes_context=True)
def include_process_data(context, process):
    """Shortcut tag for list all data from linked process models."""
    flow_class = process.flow_class

    template_names = (
        '{}/{}/process_data.html'.format(flow_class.app_label, flow_class.flow_label),
        'viewflow/workflow/process_data.html')
    template = select_template(template_names)
    context.push()
    try:
        context['process_data'] = get_object_data(process)
        context['process'] = process
        return template.render(context.flatten() if hasattr(context, 'flatten') else context)
    finally:
        context.pop()


# TODO Can we replace this with activation.method.has_permission and can_proceed?

@register.filter
def can_view(task, user):
    """Filter to check that task available to view."""

    return hasattr(task.flow_task, 'can_view') and task.flow_task.can_view(user, task)


@register.filter
def can_assign(task, user):
    """Filter to check that task available to assign."""

    return hasattr(task.flow_task, 'can_assign') and task.flow_task.can_assign(user, task)


@register.filter
def can_execute(task, user):
    """Filter to check that task available to assign."""
    return hasattr(task.flow_task, 'can_execute') and task.flow_task.can_execute(user, task)
