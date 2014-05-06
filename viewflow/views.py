from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import render, redirect

from viewflow.flow.start import StartView
from viewflow.flow.view import ProcessView, flow_view
from viewflow.shortcuts import get_page


start = StartView.as_view()
task = ProcessView.as_view()


@transaction.atomic()
def index(request, flow_cls):
    """
    Default process index view for Flow

    Lists all process instances with active tasks
    """
    process_list = flow_cls.process_cls.objects.filter(flow_cls=flow_cls) \
                                               .order_by('-created')

    templates = (
        '{}/flow/index.html'.format(flow_cls._meta.app_label),
        'viewflow/flow/index.html')

    return render(request, templates, {'process_list': get_page(request, process_list),
                                       'has_start_permission': flow_cls.start.has_perm(request.user)},
                  current_app=flow_cls._meta.namespace)


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
