from django.shortcuts import render
from django.forms.models import modelform_factory
from django.shortcuts import redirect

from viewflow.models import Process, Activation
from viewflow.shortcuts import get_page


def index(request, flow_cls):
    process_list = Process.objects.filter(flow_cls=flow_cls) \
                                  .order_by('-created')

    templates = ('{}/flow/index.html'.format(flow_cls._meta.app_label),
                 'viewflow/flow/index.html')

    return render(request, templates, {'process_list': get_page(request, process_list)},
                  current_app=flow_cls._meta.namespace)


def start(request, start_task):
    pass


def end(request, end_task, activation_id):
    pass


def task(request, flow_task, activation_id):
    activation = Activation.objects.start(activation_id, request.POST or None)
    form_cls = modelform_factory(flow_task.flow_cls.process_model)
    form = form_cls(request.POST or None)

    if form.is_valid():
        form.save()
        activation.done()
    return redirect(activation.guess_next())

    templates = ('{}/flow/index.html'.format(flow_task.flow_cls._meta.app_label),
                 'viewflow/flow/index.html')

    return render(request, templates,
                  {'form': form,
                   'activation': activation})
