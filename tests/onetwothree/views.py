from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from viewflow.models import Task
from viewflow.shortcuts import get_page


def list(request, flow_cls):
    task_list = Task.objects \
        .filter(process__flow_cls=flow_cls) \
        .select_related('process') \
        .order_by('-process__created')

    return render('onetwothree/list.html', {
        'task_list': get_page(request, task_list)
    })


def start(request, start_task):
    if not start_task.has_perm(request):
        raise PermissionDenied

    if request.method == 'POST' and 'start' in request.POST:
        activation = start_task.start_flow()
        activation.done()
        return activation.redirect_to_next()

    return render(request, 'onetwothree/start.html')


def one(request, flow_task, act_id):
    pass


def two(request, flow_task, act_id):
    pass


def three(request, flow_task, act_id):
    pass


def end(request, flow_task, act_id):
    pass
