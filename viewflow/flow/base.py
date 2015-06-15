"""
Base definitions for flow task declaration
"""
from django.conf.urls import url
from django.core.urlresolvers import reverse

from ..activation import STATUS


class ThisObject(object):
    """
    Helper for forward referencies on flow tasks
    """
    def __init__(self, name):
        self.name = name

    @property
    def owner(self):
        """
        Returns same process finished task owner
        """
        def get_task_owner(process):
            flow_cls = process.flow_cls
            task_node = flow_cls._meta.node(self.name)
            task = flow_cls.task_cls.objects.get(
                process=process,
                flow_task=task_node,
                status=STATUS.DONE)
            return task.owner
        return get_task_owner


class This(object):
    """
    Helper for building forward referenced flow task
    """
    def __getattr__(self, name):
        return ThisObject(name)


class Edge(object):
    __slots__ = ('_src', '_dst', '_edge_class', '_label')

    def __init__(self, src, dst, edge_class, label=None):
        self._src = src
        self._dst = dst
        self._edge_class = edge_class
        self._label = label

    @property
    def src(self):
        return self._src

    @property
    def dst(self):
        return self._dst

    @property
    def edge_class(self):
        return self._edge_class

    @property
    def label(self):
        return self._label

    def __str__(self):
        edge = "[%s] %s ---> %s" % (self._edge_class, self._src, self._dst)
        if self._label:
            edge += " (%s)" % self._label
        return edge


class Node(object):
    """
    Base class for flow task

    :keyword task_type: Human readable task type
    :keyword activation_cls: Activation implementation specific for this node
    """
    task_type = None
    activation_cls = None

    def __init__(self, activation_cls=None, **kwargs):
        self._incoming_edges = []

        self.flow_cls = None
        self.name = None

        if activation_cls:
            self.activation_cls = activation_cls

        super(Node, self).__init__(**kwargs)

    def _outgoing(self):
        """
        Outgoing edge iterator
        """
        raise NotImplementedError

    def _incoming(self):
        """
        Incoming edge iterator
        """
        return iter(self._incoming_edges)

    def _resolve(self, resolver):
        """
        Resolve and store outgoing links
        """

    def __str__(self):
        if self.name:
            return self.name.title().replace('_', ' ')
        return super(Node, self).__str__()

    def ready(self):
        """
        Called when flow class setup finished

        Subclasses could perform additional initialisation here
        """

    def urls(self):
        """
        List of urls for flow node views
        """
        return []

    def get_task_url(self, task, url_type, **kwargs):
        """
        Return url for the task
        """

    def activate(self, prev_activation, token):
        """
        Creates task activation
        """
        return self.activation_cls.activate(self, prev_activation, token)


class Event(Node):
    """
    Base class for event-based tasks
    """


class Task(Node):
    """
    Base class for tasks
    """


class Gateway(Node):
    """
    Base class for task gateways
    """


class NextNodeMixin(object):
    """
    Single next node mixin
    """
    def __init__(self, *args, **kwargs):
        self._next = None
        super(NextNodeMixin, self).__init__(*args, **kwargs)

    def Next(self, node):
        assert self._next is None, 'Next node already specified'
        self._next = node
        return self

    def _resolve(self, resolver):
        if self._next:
            self._next = resolver.get_implementation(self._next)

    def _outgoing(self):
        if self._next:
            yield Edge(src=self, dst=self._next, edge_class='next')


class DetailsViewMixin(object):
    def __init__(self, *args, **kwargs):
        self._details_view = kwargs.pop('details_view', None)
        super(DetailsViewMixin, self).__init__(*args, **kwargs)

    @property
    def details_view(self):
        from viewflow.views import DetailsView
        return self._details_view if self._details_view else DetailsView.as_view()

    def urls(self):
        urls = super(DetailsViewMixin, self).urls()
        urls.append(url(r'^(?P<process_pk>\d+)/{}/(?P<task_pk>\d+)/details/$'.format(self.name),
                    self.details_view, {'flow_task': self}, name="{}__details".format(self.name)))
        return urls

    def get_task_url(self, task, url_type, **kwargs):
        if url_type in ['details', 'guess']:
            url_name = '{}:{}__details'.format(self.flow_cls.instance.namespace, self.name)
            return reverse(url_name, args=[task.process_id, task.pk])
        return super(DetailsViewMixin, self).get_task_url(task, url_type, **kwargs)

    def can_view(self, user, task):
        opts = self.flow_cls.process_cls._meta
        view_perm = "{}.view_{}".format(opts.app_label, opts.model_name)
        return user.has_perm(view_perm)


class UndoViewMixin(object):
    def __init__(self, *args, **kwargs):
        self._undo_view = kwargs.pop('undo_view', None)
        super(UndoViewMixin, self).__init__(*args, **kwargs)

    @property
    def undo_view(self):
        from viewflow.views import TaskUndoView
        return self._undo_view if self._undo_view else TaskUndoView.as_view()

    def urls(self):
        urls = super(UndoViewMixin, self).urls()
        urls.append(url(r'^(?P<process_pk>\d+)/{}/(?P<task_pk>\d+)/undo/$'.format(self.name),
                    self.undo_view, {'flow_task': self}, name="{}__undo".format(self.name)))
        return urls

    def get_task_url(self, task, url_type, **kwargs):
        if url_type in ['undo']:
            url_name = '{}:{}__undo'.format(self.flow_cls.instance.namespace, self.name)
            return reverse(url_name, args=[task.process_id, task.pk])
        return super(UndoViewMixin, self).get_task_url(task, url_type, **kwargs)


class CancelViewMixin(object):
    def __init__(self, *args, **kwargs):
        self._cancel_view = kwargs.pop('cancel_view', None)
        super(CancelViewMixin, self).__init__(*args, **kwargs)

    @property
    def cancel_view(self):
        from viewflow.views import TaskCancelView
        return self._cancel_view if self._cancel_view else TaskCancelView.as_view()

    def urls(self):
        urls = super(CancelViewMixin, self).urls()
        urls.append(url(r'^(?P<process_pk>\d+)/{}/(?P<task_pk>\d+)/cancel/$'.format(self.name),
                    self.cancel_view, {'flow_task': self}, name="{}__cancel".format(self.name)))
        return urls

    def get_task_url(self, task, url_type, **kwargs):
        if url_type in ['cancel']:
            url_name = '{}:{}__cancel'.format(self.flow_cls.instance.namespace, self.name)
            return reverse(url_name, args=[task.process_id, task.pk])
        return super(CancelViewMixin, self).get_task_url(task, url_type, **kwargs)


class PerformViewMixin(object):
    def __init__(self, *args, **kwargs):
        self._perform_view = kwargs.pop('perform_view', None)
        super(PerformViewMixin, self).__init__(*args, **kwargs)

    @property
    def perform_view(self):
        from viewflow.views import TaskPerformView
        return self._perform_view if self._perform_view else TaskPerformView.as_view()

    def urls(self):
        urls = super(PerformViewMixin, self).urls()
        urls.append(url(r'^(?P<process_pk>\d+)/{}/(?P<task_pk>\d+)/perform/$'.format(self.name),
                    self.perform_view, {'flow_task': self}, name="{}__perform".format(self.name)))
        return urls

    def get_task_url(self, task, url_type, **kwargs):
        if url_type in ['perform']:
            url_name = '{}:{}__perform'.format(self.flow_cls.instance.namespace, self.name)
            return reverse(url_name, args=[task.process_id, task.pk])
        return super(PerformViewMixin, self).get_task_url(task, url_type, **kwargs)


class ActivateNextMixin(object):
    def __init__(self, *args, **kwargs):
        self._activate_next_view = kwargs.pop('activate_next_view', None)
        super(ActivateNextMixin, self).__init__(*args, **kwargs)

    @property
    def activate_next_view(self):
        from viewflow.views import TaskActivateNextView
        return self._activate_next_view if self._activate_next_view else TaskActivateNextView.as_view()

    def urls(self):
        urls = super(ActivateNextMixin, self).urls()
        urls.append(url(r'^(?P<process_pk>\d+)/{}/(?P<task_pk>\d+)/activate_next/$'.format(self.name),
                    self.activate_next_view, {'flow_task': self}, name="{}__activate_next".format(self.name)))
        return urls

    def get_task_url(self, task, url_type, **kwargs):
        if url_type in ['activate_next']:
            url_name = '{}:{}__activate_next'.format(self.flow_cls.instance.namespace, self.name)
            return reverse(url_name, args=[task.process_id, task.pk])
        return super(ActivateNextMixin, self).get_task_url(task, url_type, **kwargs)


class PermissionMixin(object):
    """
    Node mixing with permission restricted access
    """
    def __init__(self, *args, **kwargs):
        self._owner = None
        self._owner_permission = None
        self._owner_permission_auto_create = False
        self._owner_permission_help_text = None

        super(PermissionMixin, self).__init__(*args, **kwargs)

    def Permission(self, permission=None, auto_create=False, obj=None, help_text=None):
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
        if permission is None and not auto_create:
            raise ValueError('Please specify existion permission name or mark as auto_create=True')

        self._owner_permission = permission
        self._owner_permission_obj = obj
        self._owner_permission_auto_create = auto_create
        self._owner_permission_help_text = help_text

        return self

    def ready(self):
        if self._owner_permission_auto_create:
            if self._owner_permission and '.' in self._owner_permission:
                raise ValueError('Non qualified permission name expected')

            if not self._owner_permission:
                self._owner_permission = 'can_{}_{}'.format(
                    self.name, self.flow_cls.process_cls._meta.model_name)
                self._owner_permission_help_text = 'Can {}'.format(
                    self.name.replace('_', ' '))
            elif not self._owner_permission_help_text:
                self._owner_permission_help_text = self._owner_permission.replace('_', ' ').capitalize()

            for codename, _ in self.flow_cls.process_cls._meta.permissions:
                if codename == self._owner_permission:
                    break
            else:
                self.flow_cls.process_cls._meta.permissions.append(
                    (self._owner_permission, self._owner_permission_help_text))

            self._owner_permission = '{}.{}'.format(self.flow_cls.process_cls._meta.app_label, self._owner_permission)

        super(PermissionMixin, self).ready()


class TaskDescriptionMixin(object):
    """
    Extract task desctiption from view docstring
    """
    task_title = None
    task_description = None
    task_result_summary = None

    def __init__(self, view_or_cls=None, task_title=None, task_description=None, task_result_summary=None, **kwargs):
        if task_title:
            self.task_title = task_title
        if task_description:
            self.task_description = task_description
        if task_result_summary:
            self.task_result_summary = task_result_summary

        if view_or_cls:
            if view_or_cls.__doc__ and (self.task_title is None or self.task_description is None):
                docstring = view_or_cls.__doc__.split('\n\n', 1)
                if task_title is None and len(docstring) > 0:
                    self.task_title = docstring[0].strip()
                if task_description is None and len(docstring) > 1:
                    self.task_description = docstring[1].strip()
            if hasattr(view_or_cls, 'task_result_summary') and self.task_result_summary is None:
                self.task_result_summary = view_or_cls.task_result_summary

        super(TaskDescriptionMixin, self).__init__(**kwargs)


class ViewArgsMixin(object):
    """
    Capture rest of kwargs as view kwargs.
    Put this mixing always the last in inheritance order
    """
    def __init__(self, **kwargs):
        self._view_args = kwargs
