"""
Start flow task, instantiate new flow process
"""
import functools

from django.db import transaction
from django.core.urlresolvers import reverse
from django.conf.urls import url

from ..activation import Activation, StartViewActivation, STATUS
from ..exceptions import FlowRuntimeError

from . import base


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

        def __call__(self, request, flow_cls, flow_task, **kwargs):
            if self.activation:
                self.activation.initialize(flow_task, None)
                with transaction.atomic():
                    return self.func(request, **kwargs)
            else:
                activation = flow_task.activation_cls()
                activation.initialize(flow_task, None)
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
            activation = instance if isinstance(instance, StartViewActivation) else None

            return self.__class__(func, activation=activation)

    return StartViewDecorator


class ManagedStartViewActivation(StartViewActivation):
    """
    Tracks task statistics in activation form
    """
    management_form_cls = None

    def __init__(self, **kwargs):
        super(ManagedStartViewActivation, self).__init__(**kwargs)
        self.management_form = None
        self.management_form_cls = kwargs.pop('management_form_cls', None)

    def get_management_form_cls(self):
        if self.management_form_cls:
            return self.management_form_cls
        else:
            return self.flow_cls.management_form_cls

    @Activation.status.super()
    def prepare(self, data=None, user=None):
        super(ManagedStartViewActivation, self).prepare.original()
        self.task.owner = user

        management_form_cls = self.get_management_form_cls()
        self.management_form = management_form_cls(data=data, instance=self.task)

        if data:
            if not self.management_form.is_valid():
                raise FlowRuntimeError('Activation metadata is broken {}'.format(self.management_form.errors))
            self.task = self.management_form.save(commit=False)

    def has_perm(self, user):
        return self.flow_task.can_execute(user)


class BaseStart(base.TaskDescriptionViewMixin,
                base.NextNodeMixin,
                base.DetailsViewMixin,
                base.UndoViewMixin,
                base.CancelViewMixin,
                base.Event,
                base.ViewArgsMixin):
    """
    Base class for Start Process Views
    """
    task_type = 'START'
    activation_cls = ManagedStartViewActivation

    def __init__(self, view_or_cls=None, **kwargs):
        """
        Accepts view callable or CBV View class with view kwargs,
        if CBV view implements StartActivation, it used as activation_cls
        """
        self._view, self._view_cls, self._view_args = None, None, None

        if isinstance(view_or_cls, type):
            self._view_cls = view_or_cls

            if issubclass(view_or_cls, StartViewActivation):
                kwargs.setdefault('activation_cls', view_or_cls)
        else:
            self._view = view_or_cls

        super(BaseStart, self).__init__(view_or_cls=view_or_cls, **kwargs)

    @property
    def view(self):
        if not self._view:
            if not self._view_cls:
                from viewflow.views import StartProcessView
                return StartProcessView.as_view()
            else:
                self._view = self._view_cls.as_view(**self._view_args)
                return self._view
        return self._view

    def urls(self):
        urls = super(BaseStart, self).urls()
        urls.append(
            url(r'^{}/$'.format(self.name), self.view, {'flow_task': self}, name=self.name))
        return urls


class Start(base.PermissionMixin,
            base.ActivateNextMixin,
            BaseStart):
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
             if not activation.has_perm(request.user):
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

    def get_task_url(self, task, url_type='guess', **kwargs):
        if url_type in ['execute', 'guess']:
            if 'user' in kwargs and self.can_execute(kwargs['user'], task):
                url_name = '{}:{}'.format(self.flow_cls.instance.namespace, self.name)
                return reverse(url_name)

        return super(Start, self).get_task_url(task, url_type=url_type, **kwargs)

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
            if callable(self._owner_permission) and self._owner_permission(user):
                return True

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
