from django.shortcuts import render

from viewflow.models import Process
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
