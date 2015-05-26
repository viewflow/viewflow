from django.utils.six.moves.urllib.parse import quote as urlquote

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views import generic
from django.utils.http import is_safe_url

from .. import flow
from .base import get_next_task_url, task_message_user, process_message_user


class TaskViewMixin(object):
    """
    Mixin for task views, that do not implement activation interface
    """
    def get_context_data(self, **kwargs):
        context = super(TaskViewMixin, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        return context

    def get_success_url(self):
        return get_next_task_url(self.request, self.activation.process)

    def get_template_names(self):
        flow_task = self.activation.flow_task
        opts = self.activation.flow_task.flow_cls._meta

        return (
            '{}/{}/{}.html'.format(opts.app_label, opts.flow_label, flow_task.name),
            '{}/{}/task.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/task.html')

    def activation_done(self, *args, **kwargs):
        """
        Finish activation. Subclasses could override this
        """
        self.activation.done()

    def message_complete(self):
        task_message_user(self.request, self.activation.task, 'completed')
        self.activation.process.refresh_from_db()
        if self.activation.process.finished:
            process_message_user(self.request, self.activation.process, 'completed')

    def formset_valid(self, *args, **kwargs):
        """
        Called if base class is extra_views.FormsetView
        """
        super(TaskViewMixin, self).formset_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self.message_complete()
        return HttpResponseRedirect(self.get_success_url())

    def forms_valid(self, *args, **kwargs):
        """
        Called if base class is extra_views.InlinesView
        """
        super(TaskViewMixin, self).forms_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self.message_complete()
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, *args, **kwargs):
        super(TaskViewMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self.message_complete()
        return HttpResponseRedirect(self.get_success_url())

    @flow.flow_view()
    def dispatch(self, request, activation, **kwargs):
        self.activation = activation

        if not activation.prepare.can_proceed():
            task_message_user(request, activation.task, 'cannot be executed', level=messages.ERROR)
            return redirect(activation.flow_task.get_task_url(activation.task, url_type='details', user=request.user))

        if not self.activation.has_perm(request.user):
            raise PermissionDenied

        self.activation.prepare(request.POST or None)
        return super(TaskViewMixin, self).dispatch(request, **kwargs)


class TaskActivationViewMixin(object):
    """
    Mixin for views that implements activation interface
    """
    def get_context_data(self, **kwargs):
        context = super(TaskActivationViewMixin, self).get_context_data(**kwargs)
        context['activation'] = self
        return context

    def get_template_names(self):
        flow_task = self.flow_task
        opts = self.flow_task.flow_cls._meta

        return (
            '{}/{}/{}.html'.format(opts.app_label, opts.flow_label, flow_task.name),
            '{}/{}/task.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/task.html')

    def get_success_url(self):
        return get_next_task_url(self.request, self.process)

    def activation_done(self, *args, **kwargs):
        """
        Finish activation. Subclasses could override this
        """
        self.done()

    def message_complete(self):
        task_message_user(self.request, self.task, 'completed')
        self.process.refresh_from_db()
        if self.process.finished:
            process_message_user(self.request, self.process, 'completed')

    def formset_valid(self, *args, **kwargs):
        """
        Called if base class is extra_views.FormsetView
        """
        super(TaskActivationViewMixin, self).formset_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self.message_complete()
        return HttpResponseRedirect(self.get_success_url())

    def forms_valid(self, *args, **kwargs):
        """
        Called if base class is extra_views.InlinesView
        """
        super(TaskActivationViewMixin, self).forms_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self.message_complete()
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, *args, **kwargs):
        super(TaskActivationViewMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self.message_complete()
        return HttpResponseRedirect(self.get_success_url())

    @flow.flow_view()
    def dispatch(self, request, *args, **kwargs):
        if not self.prepare.can_proceed():
            messages.info(request, 'Task cannot be executed')
            return redirect(self.flow_task.get_task_url(self.task, url_type='details', user=request.user))

        if not self.has_perm(request.user):
            raise PermissionDenied

        self.prepare(request.POST or None)
        return super(TaskActivationViewMixin, self).dispatch(request, *args, **kwargs)


class ProcessView(flow.ManagedViewActivation, TaskActivationViewMixin, generic.UpdateView):
    """
    Shortcut view for task that updates subset of Process model fields
    """
    fields = []

    @property
    def model(self):
        return self.flow_cls.process_cls

    def get_object(self, queryset=None):
        return self.process


class AssignView(flow.ManagedViewActivation, generic.TemplateView):
    """
    Default assign view for flow task

    Get confirmation from user, assigns task and redirects to task pages
    """
    def get_template_names(self):
        flow_task = self.flow_task
        opts = self.flow_task.flow_cls._meta

        return (
            '{}/{}/{}_assign.html'.format(opts.app_label, opts.flow_label, flow_task.name),
            '{}/{}/task_assign.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/task_assign.html')

    def get_context_data(self, **kwargs):
        context = super(AssignView, self).get_context_data(**kwargs)
        context['activation'] = self
        return context

    def get_success_url(self):
        """
        Continue on task or redirect back to task list
        """
        url = self.flow_task.get_task_url(self.task, url_type='guess', user=self.request.user)

        back = self.request.GET.get('back', None)
        if back and not is_safe_url(url=back, host=self.request.get_host()):
            back = '/'

        if '_continue' in self.request.POST and back:
            url = "{}?back={}".format(url, urlquote(back))
        elif back:
            url = back

        return url

    def post(self, request, *args, **kwargs):
        if '_assign' or '_continue' in request.POST:
            self.assign(self.request.user)
            task_message_user(
                request, self.task,
                'assigned to {}'.format(request.user.get_full_name() or request.user.username))
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(request, *args, **kwargs)

    @flow.flow_view()
    def dispatch(self, request, *args, **kwargs):
        if not self.assign.can_proceed():
            task_message_user(request, self.task, 'cannot be assigned', level=messages.ERROR)
            return redirect(self.flow_task.get_task_url(self.task, url_type='details', user=request.user))

        if not self.flow_task.can_assign(request.user, self.task):
            raise PermissionDenied
        return super(AssignView, self).dispatch(request, *args, **kwargs)
