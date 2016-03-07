"""
Task performed by user in django view
"""
import functools

from django.core.urlresolvers import reverse
from django.conf.urls import url
from django.shortcuts import get_object_or_404

from ..activation import Activation, ViewActivation, STATUS
from ..exceptions import FlowRuntimeError
from . import base


def flow_view(**lock_args):
    """
    Decorator that locks and runs the flow view in transaction.

    Expects view with the signature `(request, activation, **kwargs)`
    or CBV view that implements TaskActivation, in this case, dispatch
    with would be called with `(request, **kwargs)`

    Returns `(request, flow_task, process_pk, task_pk, **kwargs)`
    """
    class flow_view_decorator(object):
        def __init__(self, func, activation=None):
            self.func = func
            self.activation = activation
            functools.update_wrapper(self, func)

        def __call__(self, request, flow_cls, flow_task, process_pk, task_pk, **kwargs):
            lock = flow_task.flow_cls.lock_impl(flow_task.flow_cls.instance, **lock_args)
            with lock(flow_task.flow_cls, process_pk):
                task = get_object_or_404(flow_task.flow_cls.task_cls._default_manager, pk=task_pk)

                if self.activation:
                    """
                    Class-based view that implements TaskActivation interface
                    """
                    self.activation.initialize(flow_task, task)
                    return self.func(request, **kwargs)
                else:
                    """
                    Function based view or CBV without TaskActvation interface implementation
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


class ManagedViewActivation(ViewActivation):
    """
    Tracks task statistics in activation form
    """
    management_form_cls = None

    def __init__(self, **kwargs):
        super(ManagedViewActivation, self).__init__(**kwargs)
        self.management_form = None
        self.management_form_cls = kwargs.pop('management_form_cls', None)

    def get_management_form_cls(self):
        if self.management_form_cls:
            return self.management_form_cls
        else:
            return self.flow_cls.management_form_cls

    @Activation.status.super()
    def prepare(self, data=None, user=None):
        super(ManagedViewActivation, self).prepare.original()

        if user:
            self.task.owner = user

        management_form_cls = self.get_management_form_cls()
        self.management_form = management_form_cls(data=data, instance=self.task)

        if data:
            if not self.management_form.is_valid():
                raise FlowRuntimeError('Activation metadata is broken {}'.format(self.management_form.errors))
            self.task = self.management_form.save(commit=False)

    def has_perm(self, user):
        return self.flow_task.can_execute(user, self.task)

    @classmethod
    def create_task(cls, flow_task, prev_activation, token):
        task = ViewActivation.create_task(flow_task, prev_activation, token)

        # Try to assign permission
        owner_permission = flow_task.calc_owner_permission(task)
        if owner_permission:
            task.owner_permission = owner_permission

        # Try to assign owner
        owner = flow_task.calc_owner(task)
        if owner:
            task.owner = owner
            task.status = STATUS.ASSIGNED

        return task


class BaseView(base.TaskDescriptionViewMixin,
               base.NextNodeMixin,
               base.Task,
               base.ViewArgsMixin):
    """
    Base class for ViewTasks
    """
    task_type = 'HUMAN'
    activation_cls = ManagedViewActivation

    def __init__(self, view_or_cls, **kwargs):
        """
        Accepts view callable or CBV View class with view kwargs,
        if CBV view implements ViewActivation, it used as activation_cls
        """
        self._view, self._view_cls, self._view_args = None, None, None

        if isinstance(view_or_cls, type):
            self._view_cls = view_or_cls

            if issubclass(view_or_cls, ViewActivation):
                kwargs.setdefault('activation_cls', view_or_cls)
        else:
            self._view = view_or_cls

        super(BaseView, self).__init__(view_or_cls=view_or_cls, **kwargs)

    @property
    def view(self):
        if not self._view:
            self._view = self._view_cls.as_view(**self._view_args)
        return self._view

    def urls(self):
        return [url(r'^(?P<process_pk>\d+)/{}/(?P<task_pk>\d+)/$'.format(self.name),
                    self.view, {'flow_task': self}, name=self.name)]


class View(base.PermissionMixin,
           base.UndoViewMixin,
           base.CancelViewMixin,
           base.DetailsViewMixin,
           base.ActivateNextMixin,
           BaseView):
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
    def __init__(self, *args, **kwargs):
        self._assign_view = kwargs.pop('assign_view', None)
        self._unassign_view = kwargs.pop('unassign_view', None)
        super(View, self).__init__(*args, **kwargs)

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
    def assign_view(self):
        from viewflow.views import AssignView
        return self._assign_view if self._assign_view else AssignView.as_view()

    @property
    def unassign_view(self):
        from viewflow.views import TaskUnAssignView
        return self._unassign_view if self._unassign_view else TaskUnAssignView.as_view()

    def urls(self):
        urls = super(View, self).urls()
        urls.append(url(r'^(?P<process_pk>\d+)/{}/(?P<task_pk>\d+)/assign/$'.format(self.name),
                    self.assign_view, {'flow_task': self}, name="{}__assign".format(self.name)))
        urls.append(url(r'^(?P<process_pk>\d+)/{}/(?P<task_pk>\d+)/unassign/$'.format(self.name),
                    self.unassign_view, {'flow_task': self}, name="{}__unassign".format(self.name)))
        return urls

    def get_task_url(self, task, url_type, **kwargs):
        user = kwargs.get('user', None)

        # assign
        if url_type in ['assign', 'guess']:
            if task.status == STATUS.NEW and self.can_assign(user, task):
                url_name = '{}:{}__assign'.format(self.flow_cls.instance.namespace, self.name)
                return reverse(url_name, kwargs={'process_pk': task.process_id, 'task_pk': task.pk})

        # execute
        if url_type in ['execute', 'guess']:
            if task.status == STATUS.ASSIGNED and self.can_execute(user, task):
                url_name = '{}:{}'.format(self.flow_cls.instance.namespace, self.name)
                return reverse(url_name, kwargs={'process_pk': task.process_id, 'task_pk': task.pk})

        # unassign
        if url_type in ['unassign']:
            if task.status == STATUS.ASSIGNED and self.can_unassign(user, task):
                url_name = '{}:{}__unassign'.format(self.flow_cls.instance.namespace, self.name)
                return reverse(url_name, kwargs={'process_pk': task.process_id, 'task_pk': task.pk})

        return super(View, self).get_task_url(task, url_type, **kwargs)

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

    def can_assign(self, user, task):
        # already assigned
        if task.owner_id:
            return False

        # user not logged in
        if user is None or user.is_anonymous():
            return False

        # available for everyone
        if not task.owner_permission:
            return True

        # User have the permission
        obj = None
        if self._owner_permission_obj:
            if callable(self._owner_permission_obj):
                obj = self._owner_permission_obj(task.process)
            else:
                obj = self._owner_permission_obj

        return user.has_perm(task.owner_permission, obj=obj)

    def can_unassign(self, user, task):
        # not assigned
        if task.owner_id is None:
            return False

        # user not logged in
        if user is None or user.is_anonymous():
            return False

        # Assigned to the same user
        if task.owner_id == user.pk:
            return True

        # User have flow management permissions
        return user.has_perm(self.flow_cls.instance.manage_permission_name)

    def can_execute(self, user, task):
        if task.owner_permission is None and task.owner is None:
            return True

        return task.owner == user
