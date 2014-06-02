"""
Task performed by user in django view
"""
import functools

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.views.generic.edit import UpdateView
from django.shortcuts import get_object_or_404

from viewflow.activation import ViewActivation
from viewflow.exceptions import FlowRuntimeError
from viewflow.flow.base import Task, Edge, PermissionMixin


def flow_view(**lock_args):
    """
    Decorator that locks and runs the flow view in transaction.

    Expects view with the signature `(request, activation, **kwargs)`
    or CBV view that implements ViewActivation, in this case, dispatch
    with would be called with `(request, **kwargs)`

    Returns `(request, flow_task, process_pk, task_pk, **kwargs)`
    """
    class flow_view_decorator(object):
        def __init__(self, func, activation=None):
            self.func = func
            self.activation = activation
            functools.update_wrapper(self, func)

        def __call__(self, request, flow_task, process_pk, task_pk, **kwargs):
            lock = flow_task.flow_cls.lock_impl(**lock_args)
            with lock(flow_task, process_pk):
                task = get_object_or_404(flow_task.flow_cls.task_cls._default_manager, pk=task_pk)

                if self.activation:
                    """
                    Class-based view that implements ViewActivation interface
                    """
                    self.activation.initialize(flow_task, task)
                    return self.func(request, **kwargs)
                else:
                    """
                    Function based view or CBV without ViewActvation interface implementation
                    """
                    activation = flow_task.activation_cls()
                    activation.initialize(flow_task, task)
                    return self.func(request, activation, **kwargs)

        def __get__(self, instance, instancetype):
            """
            If we decorate method on CBV that implements StartActivation interface,
            no custom activation is required.
            """
            if instance is None:
                return self

            func = self.func.__get__(instance, type)
            activation = instance if isinstance(instance, ViewActivation) else None

            return self.__class__(func, activation=activation)

    return flow_view_decorator


class TaskViewActivation(ViewActivation):
    """
    Tracks task statistics in activation form
    """
    management_form_cls = None

    def __init__(self, management_form_cls=None, **kwargs):
        super(TaskViewActivation, self).__init__(**kwargs)
        self.management_form = None
        if management_form_cls:
            self.management_form_cls = management_form_cls

    def get_management_form_cls(self):
        if self.management_form_cls:
            return self.management_form_cls
        else:
            return self.flow_cls.management_form_cls

    def prepare(self, data=None):
        super(TaskViewActivation, self).prepare()

        management_form_cls = self.get_management_form_cls()
        self.management_form = management_form_cls(data=data, instance=self.task)

        if data:
            if not self.management_form.is_valid():
                raise FlowRuntimeError('Activation metadata is broken {}'.format(self.management_form.errors))
            self.task = self.management_form.save(commit=False)


class TaskViewMixin(object):
    """
    Mixin for task views, that do not implement activation interface
    """
    def get_context_data(self, **kwargs):
        context = super(TaskViewMixin, self).get_context_data(**kwargs)
        context['activation'] = self.activation
        return context

    def get_success_url(self):
        return reverse('viewflow:index', current_app=self.activation.flow_cls._meta.namespace)

    def get_template_names(self):
        flow_task = self.activation.flow_task
        flow_cls = self.activation.flow_task.flow_cls

        return (
            '{}/flow/{}.html'.format(flow_cls._meta.app_label, flow_task.name),
            '{}/flow/task.html'.format(flow_cls._meta.app_label),
            'viewflow/flow/task.html')

    def form_valid(self, form):
        response = super(TaskViewMixin, self).form_valid(form)
        self.activation.done()
        return response

    @flow_view()
    def dispatch(self, request, activation, **kwargs):
        self.activation = activation
        if not self.activation.flow_task.has_perm(request.user, self.activation.task):
            raise PermissionDenied

        self.activation.prepare(request.POST or None)
        return super(TaskViewMixin, self).dispatch(request, **kwargs)


class ProcessView(TaskViewActivation, UpdateView):
    """
    Shortcut view for task that updates subset of Process model fields
    """
    fields = []

    @property
    def model(self):
        return self.flow_cls.process_cls

    def get_context_data(self, **kwargs):
        context = super(ProcessView, self).get_context_data(**kwargs)
        context['activation'] = self
        return context

    def get_object(self, queryset=None):
        return self.process

    def get_template_names(self):
        return (
            '{}/flow/{}.html'.format(self.flow_cls._meta.app_label, self.flow_task.name),
            '{}/flow/task.html'.format(self.flow_cls._meta.app_label),
            'viewflow/flow/task.html')

    def get_success_url(self):
        return reverse('viewflow:index', current_app=self.flow_cls._meta.namespace)

    def form_valid(self, form):
        response = super(ProcessView, self).form_valid(form)
        self.done()
        return response

    @flow_view()
    def dispatch(self, request, *args, **kwargs):
        if not self.flow_task.has_perm(request.user, self.task):
            raise PermissionDenied

        self.prepare(request.POST or None)
        return super(ProcessView, self).dispatch(request, *args, **kwargs)


class View(PermissionMixin, Task):
    """
    View task

    Example::

        task = flow.View(some_view) \\
            .Permission('my_app.can_do_task') \\
            .Next(this.next_task)

    In case of function based view::

        task = flow.Task(task)

        @flow_start_view()
        def task(request, activation):
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
    task_type = 'HUMAN'
    activation_cls = TaskViewActivation

    def __init__(self, view_or_cls, description=None, activation_cls=None, **kwargs):
        """
        Accepts view callable or CBV View class with view kwargs,
        if CBV view implements ViewActivation, it used as activation_cls
        """
        self.description = description or ""
        self._activate_next = []
        self._view, self._view_cls, self._view_args = None, None, None

        if isinstance(view_or_cls, type):
            self._view_cls = view_or_cls
            self._view_args = kwargs

            if issubclass(view_or_cls, ViewActivation):
                activation_cls = view_or_cls
        else:
            self._view = view_or_cls

        super(View, self).__init__(activation_cls=activation_cls)

    def _outgoing(self):
        for next_node in self._activate_next:
            yield Edge(src=self, dst=next_node, edge_class='next')

    def Next(self, node):
        self._activate_next.append(node)
        return self

    def Assign(self, owner=None, **owner_kwargs):
        """
        Assign task to the User immediately on activation,
        accepts user lookup kwargs or callable :: Process -> User::

            .Assign(username='employee')
            .Assign(lambda process: process.created_by)
        """
        if owner:
            self._owner = owner
        else:
            self._owner = owner_kwargs
        return self

    @property
    def view(self):
        if not self._view:
            self._view = self._view_cls.as_view(**self._view_args)
        return self._view

    @property
    def assign_view(self):
        from viewflow.views import assign
        return self._assign_view if self._assign_view else assign

    def calc_owner(self, task):
        from django.contrib.auth import get_user_model

        owner = self._owner
        if callable(owner):
            owner = owner(task.process)
        elif isinstance(owner, dict):
            owner = get_user_model() ._default_manager.get(**owner)
        return owner

    def calc_owner_permission(self, task):
        owner_permission = self._owner_permission
        if callable(owner_permission):
            owner_permission = owner_permission(task.process)
        return owner_permission

    def can_be_assigned(self, user, task):
        if task.owner_id:
            return False

        if user.is_anonymous():
            return False

        if not task.owner_permission:
            """
            Available for everyone
            """
            return True

        return user.has_perm(task.owner_permission)

    def has_perm(self, user, task):
        return task.owner == user
