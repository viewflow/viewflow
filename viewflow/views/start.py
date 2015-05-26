from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.views import generic


from .. import flow
from .base import get_next_task_url, process_message_user


class StartViewMixin(object):
    """
    Mixin for start views, that do not implement activation interface
    """
    def get_context_data(self, **kwargs):
        """
        Adds `activation` to context data
        """
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
        """
        Finish activation. Subclasses could override this
        """
        self.activation.done()

    def formset_valid(self, *args, **kwargs):
        """
        Called if base class is extra_views.FormsetView
        """
        super(StartViewMixin, self).formset_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        process_message_user(self.request, self.activation.process, 'started')
        return HttpResponseRedirect(self.get_success_url())

    def forms_valid(self, *args, **kwargs):
        """
        Called if base class is extra_views.InlinesView
        """
        super(StartViewMixin, self).forms_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        process_message_user(self.request, self.activation.process, 'started')
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, *args, **kwargs):
        super(StartViewMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        process_message_user(self.request, self.activation.process, 'started')
        return HttpResponseRedirect(self.get_success_url())

    @flow.flow_start_view()
    def dispatch(self, request, activation, **kwargs):
        """
        Check user permissions, and prepare flow to execution
        """
        self.activation = activation
        if not self.activation.has_perm(request.user):
            raise PermissionDenied

        self.activation.prepare(request.POST or None, user=request.user)
        return super(StartViewMixin, self).dispatch(request, **kwargs)


class StartActivationViewMixin(object):
    """
    Mixin for start views that implements activation interface
    """
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
        """
        Called if base class is extra_views.FormsetView
        """
        super(StartActivationViewMixin, self).formset_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        process_message_user(self.request, self.process, 'started')
        return HttpResponseRedirect(self.get_success_url())

    def forms_valid(self, *args, **kwargs):
        """
        Called if base class is extra_views.InlinesView
        """
        super(StartActivationViewMixin, self).forms_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        process_message_user(self.request, self.process, 'started')
        return HttpResponseRedirect(self.get_success_url())

    def form_valid(self, *args, **kwargs):
        """
        Called if bass class is generic.FormView
        """
        super(StartActivationViewMixin, self).form_valid(*args, **kwargs)
        self.activation_done(*args, **kwargs)
        process_message_user(self.request, self.process, 'started')
        return HttpResponseRedirect(self.get_success_url())

    @flow.flow_start_view()
    def dispatch(self, request, *args, **kwargs):
        """
        Check user permissions, and prepare flow to execution
        """
        if not self.has_perm(request.user):
            raise PermissionDenied

        self.prepare(request.POST or None, user=request.user)
        return super(StartActivationViewMixin, self).dispatch(request, *args, **kwargs)


class StartProcessView(flow.ManagedStartViewActivation, StartActivationViewMixin, generic.UpdateView):
    """
    Generic start view, allows to modify subset of process fields,
    implements :class:`viewflow.activation.StartActivation` interface
    """
    fields = []

    def get_object(self):
        return self.process
