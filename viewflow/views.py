from django.db import transaction
from django.shortcuts import render
from django.forms.models import modelform_factory
from django.views.generic.edit import UpdateView

from viewflow.shortcuts import get_page, redirect


@transaction.atomic()
def index(request, flow_cls):
    process_list = flow_cls.process_cls.objects.filter(flow_cls=flow_cls) \
                                               .order_by('-created')

    templates = ('{}/flow/index.html'.format(flow_cls._meta.app_label),
                 'viewflow/flow/index.html')

    return render(request, templates, {'process_list': get_page(request, process_list)},
                  current_app=flow_cls._meta.namespace)


@transaction.atomic()
def start(request, start_task):
    activation = start_task.start(request.POST or None)

    if request.method == 'POST' and 'start' in request.POST:
        start_task.done(activation)
        return redirect('viewflow:index', current_app=start_task.flow_cls._meta.app_label)

    templates = ('{}/flow/start.html'.format(start_task.flow_cls._meta.app_label),
                 'viewflow/flow/start.html')

    return render(request, templates,
                  {'activation': activation})


@transaction.atomic()
def end(request, end_task, activation_id):
    pass


@transaction.atomic()
def task(request, flow_task, act_id):
    flow_cls = flow_task.flow_cls

    activation = flow_task.start(act_id, request.POST or None)
    form_cls = modelform_factory(flow_cls.process_cls, exclude=["flow_cls", "finished"])
    form = form_cls(request.POST or None, instance=activation.process)

    if form.is_valid():
        form.save()
        flow_task.done(activation)
        return redirect('viewflow:index', current_app=flow_cls._meta.app_label)

    templates = ('{}/flow/task.html'.format(flow_cls._meta.app_label),
                 'viewflow/flow/task.html')

    return render(request, templates,
                  {'form': form,
                   'activation': activation},
                  current_app=flow_cls._meta.namespace)


class TaskView(UpdateView):
    pk_url_kwarg = 'act_id'
    context_object_name = 'process'

    def dispatch(self, request, *args, **kwargs):
        self.flow_task = self.kwargs['flow_task']
        self.flow_cls = self.flow_task.flow_cls
        self.process_cls = self.flow_cls.process_cls
        return super(TaskView, self).dispatch(request, *args, **kwargs)

    def get_object(self):
        act_id = self.kwargs[self.pk_url_kwarg]
        self.activation = self.flow_task.start(act_id, self.request.POST or None)
        self.process = self.process_cls.objects.get(pk=self.activation.task.process_id)
        return self.process

    def get_template_names(self):
        return ('{}/flow/task.html'.format(self.flow_cls._meta.app_label),
                'viewflow/flow/task.html')

    def get_context_data(self, **kwargs):
        context = super(TaskView, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        return context

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault('current_app', self.flow_cls._meta.namespace)
        return super(TaskView, self).render_to_response(context, **response_kwargs)

    def form_valid(self, form):
        form.save()
        self.flow_task.done(self.activation)
        return redirect('viewflow:index', current_app=self.flow_cls._meta.app_label)
