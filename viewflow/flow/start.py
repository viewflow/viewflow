"""
Start flow task, instantiate new flow process
"""
import functools

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import transaction
from django.views.generic.edit import UpdateView

from viewflow.activation import StartActivation
from viewflow.exceptions import FlowRuntimeError
from viewflow.flow.base import Event, Edge, PermissionMixin


def flow_start_view():
    """
    Decorator for start views, creates and initializes start activation

    Expects view with the signature `(request, activation, **kwargs)`
    or CBV view that implements ViewActivation, in this case, dispatch
    would be called with `(request, **kwargs)`

    Returns `(request, flow_task, **kwargs)`
    """
    class StartViewDecorator(object):
        def __init__(self, func, activation=None):
            self.func = func
            self.activation = activation
            functools.update_wrapper(self, func)

        def __call__(self, request, flow_task, **kwargs):
            if self.activation:
                self.activation.initialize(flow_task)
                with transaction.atomic():
                    return self.func(request, **kwargs)
            else:
                activation = flow_task.activation_cls()
                activation.initialize(flow_task)
                with transaction.atomic():
                    return self.func(request, activation, **kwargs)

        def __get__(self, instance, instancetype):
            """
            If we decorate method on CBV that implements StartActivation interface,
            no custom activation is required.
            """
            if instance is None:
                return self

            func = self.func.__get__(instance, type)
            activation = instance if isinstance(instance, StartActivation) else None

            return self.__class__(func, activation=activation)

    return StartViewDecorator


class StartViewActivation(StartActivation):
    """
    Tracks task statistics in activation form
    """
    management_form_cls = None

    def __init__(self, management_form_cls=None, **kwargs):
        super(StartViewActivation, self).__init__(**kwargs)
        self.management_form = None
        if management_form_cls:
            self.management_form_cls = management_form_cls

    def get_management_form_cls(self):
        if self.management_form_cls:
            return self.management_form_cls
        else:
            return self.flow_cls.management_form_cls

    def prepare(self, data=None):
        super(StartViewActivation, self).prepare()

        management_form_cls = self.get_management_form_cls()
        self.management_form = management_form_cls(data=data, instance=self.task)

        if data:
            if not self.management_form.is_valid():
                raise FlowRuntimeError('Activation metadata is broken {}'.format(self.management_form.errors))
            self.task = self.management_form.save(commit=False)


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
        """
        Redirects to flow index page
        """
        return reverse('viewflow:index', current_app=self.activation.flow_cls._meta.namespace)

    def get_template_names(self):
        """
        Get template names, first `app_name/flow/start.html` would be checked,
        and if it is missing, standard `viewflow/flow/start.html` will be used
        """
        return ('{}/flow/start.html'.format(self.activation.flow_cls._meta.app_label),
                'viewflow/flow/start.html')

    def form_valid(self, form):
        response = super(StartViewMixin, self).form_valid(form)
        self.activation.done()
        return response

    @flow_start_view()
    def dispatch(self, request, activation, **kwargs):
        """
        Check user permissions, and prepare flow to execution
        """
        self.activation = activation
        if not self.activation.flow_task.has_perm(request.user):
            raise PermissionDenied

        self.activation.prepare(request.POST or None)
        return super(StartViewMixin, self).dispatch(request, **kwargs)


class StartView(StartViewActivation, UpdateView):
    """
    Generic start view, allows to modify subset of process fields,
    implements :class:`viewflow.activation.StartActivation` interface
    """
    fields = []

    @property
    def model(self):
        """
        Returns process class
        """
        return self.flow_cls.process_cls

    def get_context_data(self, **kwargs):
        """
        Adds `activation` to context data
        """
        context = super(StartView, self).get_context_data(**kwargs)
        context['activation'] = self
        return context

    def get_object(self):
        """
        Returns process instance
        """
        return self.process

    def get_template_names(self):
        """
        Get template names, first `app_name/flow/start.html` would be checked,
        and if it is missing, standard `viewflow/flow/start.html` will be used
        """
        return ('{}/flow/start.html'.format(self.flow_cls._meta.app_label),
                'viewflow/flow/start.html')

    def get_success_url(self):
        """
        Redirects to flow index page
        """
        return reverse('viewflow:index', current_app=self.flow_cls._meta.app_label)

    def form_valid(self, form):
        response = super(StartView, self).form_valid(form)
        self.done(process=self.object, user=self.request.user)
        return response

    @flow_start_view()
    def dispatch(self, request, *args, **kwargs):
        """
        Check user permissions, and prepare flow to execution
        """
        if not self.flow_task.has_perm(request.user):
            raise PermissionDenied

        self.prepare(request.POST or None)
        return super(StartView, self).dispatch(request, *args, **kwargs)


class Start(PermissionMixin, Event):
    """
    Start process event

    Example::

        start = flow.Start(StartView, fields=["some_process_field"]) \\
            .Available(lambda user: user.is_super_user) \\
            .Activate(this.first_start)

    In case of function based view::

        start = flow.Start(start_process)

        @flow_start_view()
        def start_process(request, activation):
             if not activation.flow_task.has_perm(request.user):
                 raise PermissionDenied

             activation.prepare(request.POST or None)
             form = SomeForm(request.POST or None)

             if form.is_valid():
                  form.save()
                  activation.done()
                  return redirect('/')
             return render(request, {'activation': activation, 'form': form})

    Ensure to include `{{ activation.management_form }}` inside template, to proper
    track when task was started and other task performance statistics::

             <form method="POST">
                  {{ form }}
                  {{ activation.management_form }}
                  <button type="submit"/>
             </form>
    """
    task_type = 'START'
    activation_cls = StartViewActivation

    def __init__(self, view_or_cls=None, activation_cls=None, **kwargs):
        """
        Accepts view callable or CBV View class with view kwargs,
        if CBV view implements StartActivation, it used as activation_cls
        """
        self._activate_next = []
        self._view, self._view_cls, self._view_args = None, None, None

        if isinstance(view_or_cls, type):
            self._view_cls = view_or_cls
            self._view_args = kwargs

            if issubclass(view_or_cls, StartActivation):
                activation_cls = view_or_cls
        else:
            self._view = view_or_cls

        super(Start, self).__init__(activation_cls=activation_cls)

    def _outgoing(self):
        for next_node in self._activate_next:
            yield Edge(src=self, dst=next_node, edge_class='next')

    def Activate(self, node):
        self._activate_next.append(node)
        return self

    def Available(self, owner=None, **owner_kwargs):
        """
        Make process start action available for the User
        accepts user lookup kwargs or callable predicate :: User -> bool::

            .Available(username='employee')
            .Available(lambda user: user.is_super_user)
        """
        if owner:
            self._owner = owner
        else:
            self._owner = owner_kwargs
        return self

    @property
    def view(self):
        if not self._view:
            if not self._view_cls:
                from viewflow.views import start
                return start
            else:
                self._view = self._view_cls.as_view(**self._view_args)
                return self._view
        return self._view

    def has_perm(self, user):
        from django.contrib.auth import get_user_model

        if self._owner:
            if callable(self._owner) and self._owner(user):
                return True
            owner = get_user_model()._default_manager.get(**self._owner)
            return owner == user

        elif self._owner_permission:
            if callable(self._owner_permission) and self._owner_permission(user):
                return True
            return user.has_perm(self._owner_permission)

        else:
            """
            No restriction
            """
            return True
