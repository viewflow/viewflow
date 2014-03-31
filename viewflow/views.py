from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django.views.generic.edit import UpdateView

from viewflow.shortcuts import get_page, redirect


@transaction.atomic()
def index(request, flow_cls):
    process_list = flow_cls.process_cls.objects.filter(flow_cls=flow_cls) \
                                               .order_by('-created')

    templates = ('{}/flow/index.html'.format(flow_cls._meta.app_label),
                 'viewflow/flow/index.html')

    return render(request, templates, {'process_list': get_page(request, process_list),
                                       'has_start_permission': flow_cls.start.has_perm(request.user)},
                  current_app=flow_cls._meta.namespace)


@transaction.atomic()
def start(request, start_task):
    if not start_task.has_perm(request.user):
        raise PermissionDenied

    activation = start_task.start(request.POST or None)

    if request.method == 'POST' and 'start' in request.POST:
        start_task.done(activation)
        return redirect('viewflow:index', current_app=start_task.flow_cls._meta.app_label)

    templates = ('{}/flow/start.html'.format(start_task.flow_cls._meta.app_label),
                 'viewflow/flow/start.html')

    return render(request, templates,
                  {'activation': activation})


@transaction.atomic()
def assign(request, view_task, act_id):
    task = get_object_or_404(view_task.flow_cls.task_cls, pk=act_id)

    if not view_task.can_be_assigned(request.user, task):
        raise PermissionDenied

    activation = view_task.get(task)

    if request.method == 'POST' and 'assign' in request.POST:
        view_task.assign(activation, request.user)
        return redirect(activation.task)

    templates = ('{}/flow/assign.html'.format(view_task.flow_cls._meta.app_label),
                 'viewflow/flow/assign.html')

    return render(request, templates,
                  {'activation': activation})


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
        self.task = get_object_or_404(self.flow_cls.task_cls, pk=act_id)
        self.process = self.process_cls.objects.get(pk=self.task.process_id)

        if not self.flow_task.has_perm(self.request.user, self.task):
            raise PermissionDenied

        self.activation = self.flow_task.start(self.task, self.request.POST or None)

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
