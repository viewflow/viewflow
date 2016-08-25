from copy import copy

from django.conf.urls import url
from django.core.urlresolvers import reverse

from .. import Event, Task, mixins
from ..activation import StartActivation, ViewActivation, STATUS


class BaseStart(mixins.TaskDescriptionViewMixin,
                mixins.NextNodeMixin,
                mixins.ActivateNextMixin,
                mixins.DetailViewMixin,
                mixins.UndoViewMixin,
                mixins.CancelViewMixin,
                Event,
                mixins.ViewArgsMixin):
    task_type = 'START'
    start_view_class = None

    def __init__(self, view_or_class=None, **kwargs):
        """
        Accepts view callable or CBV View class with view kwargs,
        if CBV view implements StartActivation, it used as activation_class
        """
        self._view, self._view_class, self._view_args = None, None, None

        if isinstance(view_or_class, type):
            self._view_class = view_or_class

            if issubclass(view_or_class, StartActivation):
                kwargs.setdefault('activation_class', view_or_class)
        else:
            self._view = view_or_class

        super(BaseStart, self).__init__(view_or_class=view_or_class, **kwargs)

    @property
    def view(self):
        if not self._view:
            if not self._view_class:
                return self.start_view_class.as_view()
            else:
                self._view = self._view_class.as_view(**self._view_args)
                return self._view
        return self._view

    def urls(self):
        urls = super(BaseStart, self).urls()
        urls.append(
            url(r'^{}/$'.format(self.name), self.view, {'flow_task': self}, name=self.name))
        return urls


class Start(mixins.PermissionMixin, BaseStart):
    activation_class = StartActivation

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

    def get_task_url(self, task, url_type='guess', namespace='',  **kwargs):
        if url_type in ['execute', 'guess']:
            if 'user' in kwargs and self.can_execute(kwargs['user'], task):
                url_name = '{}:{}'.format(namespace, self.name)
                return reverse(url_name)

        return super(BaseStart, self).get_task_url(task, url_type=url_type, namespace=namespace, **kwargs)

    def can_execute(self, user, task=None):
        if task and task.status != STATUS.NEW:
            return False

        from django.contrib.auth import get_user_model

        if self._owner:
            if callable(self._owner):
                return self._owner(user)
            else:
                owner = get_user_model()._default_manager.get(**self._owner)
                return owner == user

        elif self._owner_permission:
            obj = None
            if self._owner_permission_obj:
                if callable(self._owner_permission_obj):
                    obj = self._owner_permission_obj()
                else:
                    obj = self._owner_permission_obj

            return user.has_perm(self._owner_permission, obj=obj)

        else:
            """
            No restriction
            """
            return True


class BaseView(mixins.TaskDescriptionViewMixin,
               mixins.NextNodeMixin,
               mixins.ActivateNextMixin,
               mixins.DetailViewMixin,
               mixins.UndoViewMixin,
               mixins.CancelViewMixin,
               Task,
               mixins.ViewArgsMixin):
    """
    Base class for ViewTasks
    """
    task_type = 'HUMAN'
    task_view_class = None

    def __init__(self, view_or_class, **kwargs):
        """
        Accepts view callable or CBV View class with view kwargs,
        if CBV view implements ViewActivation, it used as activation_class
        """
        self._view, self._view_class, self._view_args = None, None, None

        if isinstance(view_or_class, type):
            self._view_class = view_or_class

            if issubclass(view_or_class, ViewActivation):
                kwargs.setdefault('activation_class', view_or_class)
        else:
            self._view = view_or_class

        super(BaseView, self).__init__(view_or_class=view_or_class, **kwargs)

    @property
    def view(self):
        if not self._view:
            self._view = self._view_class.as_view(**self._view_args)
        return self._view

    def urls(self):
        urls = super(BaseView, self).urls()
        urls.append(
            url(r'^(?P<process_pk>\d+)/{}/(?P<task_pk>\d+)/$'.format(self.name),
                self.view, {'flow_task': self}, name=self.name)
        )
        return urls


class View(mixins.PermissionMixin, BaseView):
    activation_class = ViewActivation
    assign_view_class = None
    unassign_view_class = None

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
        result = copy(self)

        if owner:
            result._owner = owner
        else:
            result._owner = owner_kwargs
        return result

    @property
    def assign_view(self):
        return self._assign_view if self._assign_view else self.assign_view_class.as_view()

    @property
    def unassign_view(self):
        return self._unassign_view if self._unassign_view else self.unassign_view_class.as_view()

    def urls(self):
        urls = super(View, self).urls()
        urls.append(url(r'^(?P<process_pk>\d+)/{}/(?P<task_pk>\d+)/assign/$'.format(self.name),
                    self.assign_view, {'flow_task': self}, name="{}__assign".format(self.name)))
        urls.append(url(r'^(?P<process_pk>\d+)/{}/(?P<task_pk>\d+)/unassign/$'.format(self.name),
                    self.unassign_view, {'flow_task': self}, name="{}__unassign".format(self.name)))
        return urls

    def get_task_url(self, task, url_type='guess', namespace='', **kwargs):
        user = kwargs.get('user', None)

        # assign
        if url_type in ['assign', 'guess']:
            if task.status == STATUS.NEW and self.can_assign(user, task):
                url_name = '{}:{}__assign'.format(namespace, self.name)
                return reverse(url_name, kwargs={'process_pk': task.process_id, 'task_pk': task.pk})

        # execute
        if url_type in ['execute', 'guess']:
            if task.status == STATUS.ASSIGNED and self.can_execute(user, task):
                url_name = '{}:{}'.format(namespace, self.name)
                return reverse(url_name, kwargs={'process_pk': task.process_id, 'task_pk': task.pk})

        # unassign
        if url_type in ['unassign']:
            if task.status == STATUS.ASSIGNED and self.can_unassign(user, task):
                url_name = '{}:{}__unassign'.format(namespace, self.name)
                return reverse(url_name, kwargs={'process_pk': task.process_id, 'task_pk': task.pk})

        return super(View, self).get_task_url(task, url_type, namespace=namespace, **kwargs)

    def calc_owner(self, activation):
        from django.contrib.auth import get_user_model

        owner = self._owner
        if callable(owner):
            owner = owner(activation)
        elif isinstance(owner, dict):
            owner = get_user_model() ._default_manager.get(**owner)
        return owner

    def calc_owner_permission(self, activation):
        owner_permission = self._owner_permission
        if callable(owner_permission):
            owner_permission = owner_permission(activation)
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
        return user.has_perm(self.flow_class.instance.manage_permission_name)

    def can_execute(self, user, task):
        if task.owner_permission is None and task.owner is None:
            return True

        return task.owner == user
