from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.views import generic
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from .. import flow
from .base import get_next_task_url, get_process_hyperlink


class StartViewMixin(object):

    """Mixin for start views, that do not implement activation interface."""

    def get_context_data(self, **kwargs):
        """Add ``activation`` to context data."""
        context = super(StartViewMixin, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        return context

    def get_success_url(self):
        return get_next_task_url(self.request, self.activation.process)

    def get_template_names(self):
        flow_task = self.activation.flow_task
        opts = self.activation.flow_task.flow_cls._meta

        return (
            '{}/{}/{}.html'.format(opts.app_label, opts.flow_label, flow_task.name),
            '{}/{}/start.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/start.html')

    def activation_done(self, *args, **kwargs):
        """Finish activation."""
        self.activation.done()

    def formset_valid(self, *args, **kwargs):
        """Called if base class is :class:`extra_views.FormsetView`."""
        super(StartViewMixin, self).formset_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self._message_process_started()
        return HttpResponseRedirect(self.get_success_url())

    def forms_valid(self, *args, **kwargs):
        """Called if base class is :class:`extra_views.InlineView`."""
        super(StartViewMixin, self).forms_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self._message_process_started()
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, *args, **kwargs):
        super(StartViewMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self._message_process_started()
        return HttpResponseRedirect(self.get_success_url())

    @flow.flow_start_view()
    def dispatch(self, request, activation, **kwargs):
        """Check user permissions, and prepare flow to execution."""
        self.activation = activation
        if not self.activation.has_perm(request.user):
            raise PermissionDenied

        self.activation.prepare(request.POST or None, user=request.user)
        return super(StartViewMixin, self).dispatch(request, **kwargs)

    def _message_process_started(self):
        hyperlink = get_process_hyperlink(self.activation.process)
        msg = _('Process {hyperlink} has been started.').format(hyperlink=hyperlink)
        messages.info(self.request, mark_safe(msg), fail_silently=True)


class StartActivationViewMixin(object):

    """Mixin for start views that implements activation interface."""

    def get_context_data(self, **kwargs):
        context = super(StartActivationViewMixin, self).get_context_data(**kwargs)
        context['activation'] = self
        return context

    def get_template_names(self):
        flow_task = self.flow_task
        opts = self.flow_task.flow_cls._meta

        return (
            '{}/{}/{}.html'.format(opts.app_label, opts.flow_label, flow_task.name),
            '{}/{}/start.html'.format(opts.app_label, opts.flow_label),
            'viewflow/flow/start.html')

    def get_success_url(self):
        return get_next_task_url(self.request, self.process)

    def activation_done(self, *args, **kwargs):
        self.done()

    def formset_valid(self, *args, **kwargs):
        """Called if base class is :class:`extra_views.FormsetView`."""
        super(StartActivationViewMixin, self).formset_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self._message_process_started()
        return HttpResponseRedirect(self.get_success_url())

    def forms_valid(self, *args, **kwargs):
        """Called if base class is :class:`extra_views.InlineView`."""
        super(StartActivationViewMixin, self).forms_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self._message_process_started()
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, *args, **kwargs):
        """Called if bass class is :class:`.generic.FormView`."""
        super(StartActivationViewMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        self._message_process_started()
        return HttpResponseRedirect(self.get_success_url())

    @flow.flow_start_view()
    def dispatch(self, request, *args, **kwargs):
        """Check user permissions, and prepare flow to execution."""
        if not self.has_perm(request.user):
            raise PermissionDenied

        self.prepare(request.POST or None, user=request.user)
        return super(StartActivationViewMixin, self).dispatch(request, *args, **kwargs)

    def _message_process_started(self):
        hyperlink = get_process_hyperlink(self.process)
        msg = _('Process {hyperlink} has been started.').format(hyperlink=hyperlink)
        messages.info(self.request, mark_safe(msg), fail_silently=True)


class StartProcessView(flow.ManagedStartViewActivation, StartActivationViewMixin, generic.UpdateView):
    fields = []

    def get_object(self):
        return self.process
