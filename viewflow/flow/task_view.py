"""
Task performed by user in django view
"""
import functools

from django.shortcuts import get_object_or_404

from viewflow.activation import ViewActivation
from viewflow.exceptions import FlowRuntimeError
from viewflow.flow.base import Task, Edge, PermissionMixin, TaskDescriptionMixin


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


class View(PermissionMixin, TaskDescriptionMixin, Task):
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
        self._assign_view = None

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

    def Permission(self, permission=None, assign_view=None, auto_create=False, help_text=None):
        """
        Make task available for users with specific permission,
        aceps permissions name of callable :: Process -> permission_name::

            .Permission('my_app.can_approve')
            .Permission(lambda process: 'my_app.department_manager_{}'.format(process.depratment.pk))

        Task specific permission could be auto created during migration::

            # Creates `processcls_app.can_do_task_processcls` permission
            do_task = View().Permission(auto_create=True)

            # You can specify permission codename and description right here
            # The following creates `processcls_app.can_execure_task` permission
            do_task = View().Permission('can_execute_task', help_text='Custom text', auto_create=True)
        """

        self._assign_view = assign_view

        return super(View, self).Permission(
            permission=permission,
            auto_create=auto_create,
            help_text=help_text)

    @property
    def view(self):
        if not self._view:
            self._view = self._view_cls.as_view(**self._view_args)
        return self._view

    @property
    def assign_view(self):
        from viewflow.views import AssignView
        return self._assign_view if self._assign_view else AssignView.as_view()

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
