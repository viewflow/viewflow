from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect

from viewflow.flow.start import StartView
from viewflow.flow.view import ProcessView, flow_view


start = StartView.as_view()
task = ProcessView.as_view()


@flow_view()
def assign(request, activation):
    """
    Default assign view for flow task

    Get confirmation from user, assigns task and redirects to task pages
    """
    if not activation.flow_task.can_be_assigned(request.user, activation.task):
        raise PermissionDenied

    if request.method == 'POST' and 'assign' in request.POST:
        activation.assign(request.user)
        return redirect(activation.task)

    templates = (
        '{}/flow/{}_assign.html'.format(activation.flow_task.flow_cls._meta.app_label, activation.flow_task.name),
        '{}/flow/assign.html'.format(activation.flow_task.flow_cls._meta.app_label),
        'viewflow/flow/assign.html')

    return render(request, templates,
                  {'activation': activation})
