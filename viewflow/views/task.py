from urllib.parse import quote as urlquote
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
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
        flow_cls = self.activation.flow_task.flow_cls

        return (
            '{}/flow/{}.html'.format(flow_cls._meta.app_label, flow_task.name),
            '{}/flow/task.html'.format(flow_cls._meta.app_label),
            'viewflow/flow/task.html')

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault('current_app', self.activation.flow_cls._meta.namespace)
        return super(TaskViewMixin, self).render_to_response(context, **response_kwargs)

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
        if not self.activation.flow_task.has_perm(request.user, self.activation.task):
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
        return (
            '{}/flow/{}.html'.format(self.flow_cls._meta.app_label, self.flow_task.name),
            '{}/flow/task.html'.format(self.flow_cls._meta.app_label),
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

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault('current_app', self.flow_cls._meta.namespace)
        return super(TaskActivationViewMixin, self).render_to_response(context, **response_kwargs)

    @flow.flow_view()
    def dispatch(self, request, *args, **kwargs):
        if not self.flow_task.has_perm(request.user, self.task):
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
        return (
            '{}/flow/{}_assign.html'.format(self.flow_task.flow_cls._meta.app_label, self.flow_task.name),
            '{}/flow/assign.html'.format(self.flow_task.flow_cls._meta.app_label),
            'viewflow/flow/assign.html')

    def get_context_data(self, **kwargs):
        context = super(AssignView, self).get_context_data(**kwargs)
        context['activation'] = self
        return context

    def get_success_url(self):
        url = self.task.get_absolute_url()
        if 'back' in self.request.GET:
            url = "{}?back={}".format(url, urlquote(self.request.GET['back']))
        return url

    def activation_assign(self):
        self.assign(self.request.user)

    def post(self, request, *args, **kwargs):
        if 'assign' in request.POST:
            self.activation_assign()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.get(request, *args, **kwargs)

    @flow.flow_view()
    def dispatch(self, request, *args, **kwargs):
        if not self.flow_task.can_be_assigned(request.user, self.task):
            raise PermissionDenied
        return super(AssignView, self).dispatch(request, *args, **kwargs)
