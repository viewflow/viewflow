from itertools import groupby
from django.core.exceptions import PermissionDenied
from django.shortcuts import render

from viewflow.models import Task


def list(request, flow_cls):
    task_list = Task.objects \
        .filter(process__flow_cls=flow_cls) \
        .select_related('process') \
        .order_by('process_id')

    if 'finished' in request.GET:
        task_list = task_list.filter(finished__isnull=True)
    else:
        task_list = task_list.filter(finished__isnull=False)

    process_list = groupby(task_list, lambda task: task.process)

    return render('onetwothree/list.html', {
        'process_list': process_list
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
