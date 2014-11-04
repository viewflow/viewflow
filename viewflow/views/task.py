from urllib.parse import quote as urlquote

from django_fsm import can_proceed
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.views import generic

from .. import flow
from .base import get_next_task_url


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

    def formset_valid(self, *args, **kwargs):
        """
        Called if base class is extra_views.FormsetView
        """
        super(TaskViewMixin, self).formset_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())

    def forms_valid(self, *args, **kwargs):
        """
        Called if base class is extra_views.InlinesView
        """
        super(TaskViewMixin, self).forms_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, *args, **kwargs):
        super(TaskViewMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())

    @flow.flow_view()
    def dispatch(self, request, activation, **kwargs):
        self.activation = activation

        if not can_proceed(activation.task.prepare):
            messages.info(request, 'Task cannot be executed')
            return redirect(activation.task.get_absolute_url(user=request.user, url_type='details'))

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

    def formset_valid(self, *args, **kwargs):
        """
        Called if base class is extra_views.FormsetView
        """
        super(TaskActivationViewMixin, self).formset_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())

    def forms_valid(self, *args, **kwargs):
        """
        Called if base class is extra_views.InlinesView
        """
        super(TaskActivationViewMixin, self).forms_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, *args, **kwargs):
        super(TaskActivationViewMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        return HttpResponseRedirect(self.get_success_url())

    @flow.flow_view()
    def dispatch(self, request, *args, **kwargs):
        if not can_proceed(self.task.prepare):
            messages.info(request, 'Task cannot be executed')
            return redirect(self.task.get_absolute_url(user=request.user, url_type='details'))

        if not self.has_perm(request.user):
            raise PermissionDenied

        self.prepare(request.POST or None)
        return super(TaskActivationViewMixin, self).dispatch(request, *args, **kwargs)


class ProcessView(flow.TaskViewActivation, TaskActivationViewMixin, generic.UpdateView):
    """
    Shortcut view for task that updates subset of Process model fields
    """
    fields = []

    @property
    def model(self):
        return self.flow_cls.process_cls

    def get_object(self, queryset=None):
        return self.process


class AssignView(flow.TaskViewActivation, generic.TemplateView):
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
        url = self.task.get_absolute_url(user=self.request.user)
        if 'back' in self.request.GET:
            url = "{}?back={}".format(url, urlquote(self.request.GET['back']))
        return url

    def activation_assign(self):
        self.task.assign(user=self.request.user)
        self.task.save()

    def post(self, request, *args, **kwargs):
        if 'assign' in request.POST:
            self.activation_assign()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(request, *args, **kwargs)

    @flow.flow_view()
    def dispatch(self, request, *args, **kwargs):
        if not can_proceed(self.task.assign):
            messages.info(request, 'Task cannot be assigned')
            return redirect(self.task.get_absolute_url(user=request.user))

        if not self.flow_task.can_assign(request.user, self.task):
            raise PermissionDenied
        return super(AssignView, self).dispatch(request, *args, **kwargs)
