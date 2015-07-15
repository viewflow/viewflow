from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.http import is_safe_url
from django.utils.safestring import mark_safe

from django.views import generic

from .. import flow, activation


def get_next_task_url(request, process):
    """
    Heruistic for user on complete task redirect
    """
    if '_continue' in request.POST:
        # Try to find next task available for the user
        task_cls = process.flow_cls.task_cls

        user_tasks = task_cls._default_manager \
            .filter(process=process, owner=request.user, status=activation.STATUS.ASSIGNED)

        if user_tasks.exists():
            task = user_tasks.first()
            return task.flow_task.get_task_url(task, url_type='guess', user=request.user)
        else:
            user_tasks = task_cls._default_manager.user_queue(request.user)\
                .filter(process=process, status=activation.STATUS.NEW)
            if user_tasks.exists():
                task = user_tasks.first()
                return task.flow_task.get_task_url(task, url_type='guess', user=request.user)

    elif 'back' in request.GET:
        # Back to task list
        back_url = request.GET['back']
        if not is_safe_url(url=back_url, host=request.get_host()):
            back_url = '/'
        return back_url

    # Back to process list
    if process and process.pk:
        return reverse('{}:details'.format(process.flow_cls.instance.namespace),
                       kwargs={'process_pk': process.pk})
    else:
        return reverse('{}:index'.format(process.flow_cls.instance.namespace))


def process_message_user(request, process, message, level=messages.SUCCESS):
    """
    Message to the user prefixed with process link
    """
    process_url = reverse('{}:details'.format(process.flow_cls.instance.namespace), kwargs={'process_pk': process.pk})
    message = 'Process <a href="{}">{}</a> {}'.format(process_url, process.pk, message)
    messages.add_message(request, level, mark_safe(message))


def task_message_user(request, task, message, level=messages.SUCCESS):
    """
    Message to the user prefixed with task link
    """
    task_url = task.flow_task.get_task_url(task, url_type='details', user=request.user)
    message = 'Task <a href="{}">{}</a> {}'.format(task_url, task.pk, message)
    messages.add_message(request, level, mark_safe(message))


def tasks_message_user(request, tasks, message, level=messages.SUCCESS):
    """
    Message to the user prefixed with task link
    """
    tasks_message = []
    for task in tasks:
        task_url = task.flow_task.get_task_url(task, url_type='details', user=request.user)
        tasks_message.append('<a href="{}">{}</a>'.format(task_url, task.pk))

    message = "Tasks {} {}".format(' '.join(tasks_message), message)
    messages.add_message(request, level, mark_safe(message))


class FlowViewPermissionMixin(object):
    flow_cls = None

    def dispatch(self, *args, **kwargs):
        self.flow_cls = kwargs.get('flow_cls', self.flow_cls)
        return permission_required(self.flow_cls.instance.view_permission_name)(
            super(FlowViewPermissionMixin, self).dispatch)(*args, **kwargs)


class FlowManagePermissionMixin(object):
    flow_cls = None

    def dispatch(self, *args, **kwargs):
        self.flow_cls = kwargs.get('flow_cls', self.flow_cls)
        return permission_required(self.flow_cls.instance.manage_permission_name)(
            super(FlowManagePermissionMixin, self).dispatch)(*args, **kwargs)


class DetailsView(generic.TemplateView):
    """
    Default details view for flow task

    Get confirmation from user, assigns task and redirects to task pages
    """
    def get_template_names(self):
        flow_task = self.activation.flow_task
        opts = self.activation.flow_task.flow_cls._meta

        return (
            '{}/{}/{}_details.html'.format(opts.app_label, opts.flow_label, flow_task.name),
            '{}/{}/task_details.html'.format(opts.app_label, opts.flow_label),
            '{}/flow/{}_details.html'.format(opts.app_label, flow_task.name),
            '{}/flow/task_details.html'.format(opts.app_label),
            'viewflow/flow/task_details.html')

    def get_context_data(self, **kwargs):
        context = super(DetailsView, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        return context

    @flow.flow_view()
    def dispatch(self, request, activation, *args, **kwargs):
        self.activation = activation

        if not self.activation.flow_task.can_view(request.user, self.activation.task):
            raise PermissionDenied
        return super(DetailsView, self).dispatch(request, *args, **kwargs)


class BaseTaskActionView(FlowManagePermissionMixin, generic.TemplateView):
    flow_cls = None
    action_name = None

    def can_proceed(self):
        raise NotImplementedError

    def perform(self):
        raise NotImplementedError

    def get_template_names(self):
        flow_task = self.activation.flow_task
        opts = self.activation.flow_task.flow_cls._meta

        return (
            '{}/{}/{}_{}.html'.format(opts.app_label, opts.flow_label, flow_task.name, self.action_name),
            '{}/{}/task_{}.html'.format(opts.app_label, opts.flow_label, self.action_name),
            '{}/flow/{}_{}.html'.format(opts.app_label, flow_task.name, self.action_name),
            '{}/flow/task_{}.html'.format(opts.app_label, self.action_name),
            'viewflow/flow/task_{}.html'.format(self.action_name),
            'viewflow/flow/task_action.html')

    def get_success_url(self):
        return self.activation.flow_task.get_task_url(self.activation.task, 'details', user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super(BaseTaskActionView, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        context['flow_cls'] = self.flow_cls
        return context

    def post(self, request, *args, **kwargs):
        if 'run_action' in request.POST:
            self.perform()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(request, *args, **kwargs)

    @flow.flow_view()
    def dispatch(self, request, activation, **kwargs):
        self.flow_cls = activation.flow_cls
        self.activation = activation

        if not self.can_proceed():
            task_message_user(
                request, activation.task, "Can't execute action {}".format(self.action_name.title),
                level=messages.ERROR)
            return redirect(activation.flow_task.get_task_url(activation.task, url_type='details', user=request.user))

        return super(BaseTaskActionView, self).dispatch(request, **kwargs)
