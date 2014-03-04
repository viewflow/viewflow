from django.shortcuts import render
from django.forms.models import modelform_factory

from viewflow.models import Process
from viewflow.shortcuts import get_page, redirect


def index(request, flow_cls):
    process_list = Process.objects.filter(flow_cls=flow_cls) \
                                  .order_by('-created')

    templates = ('{}/flow/index.html'.format(flow_cls._meta.app_label),
                 'viewflow/flow/index.html')

    return render(request, templates, {'process_list': get_page(request, process_list)},
                  current_app=flow_cls._meta.namespace)


def start(request, start_task):
    activation = start_task.start(request.POST or None)

    if request.method == 'POST' and 'start' in request.POST:
        start_task.done(activation)
        return redirect('viewflow:index', current_app=start_task.flow_cls._meta.app_label)

    templates = ('{}/flow/start.html'.format(start_task.flow_cls._meta.app_label),
                 'viewflow/flow/start.html')

    return render(request, templates,
                  {'activation': activation})


def end(request, end_task, activation_id):
    pass


def task(request, flow_task, activation_id):
    activation = flow_task.start(activation_id, request.POST or None)
    form_cls = modelform_factory(flow_task.flow_cls.process_model)
    form = form_cls(request.POST or None)

    if form.is_valid():
        form.save()
        flow_task.done(activation)
        return redirect('viewflow:index', current_app=flow_task.flow_cls._meta.app_label)

    templates = ('{}/flow/task.html'.format(flow_task.flow_cls._meta.app_label),
                 'viewflow/flow/task.html')

    return render(request, templates,
                  {'form': form,
                   'activation': activation})
