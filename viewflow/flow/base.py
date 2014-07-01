"""
Base definitions for flow task declaration
"""


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
                status=flow_cls.task_cls.STATUS.FINISHED)
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

    def __str__(self):
        if self.name:
            return self.name.title().replace('_', ' ')
        return super(Node, self).__str__()

    def ready(self):
        """
        Called when flow class setup finished

        Subclasses could perform additional initialisation here
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


class PermissionMixin(object):
    """
    Node mixing with permission restricted access
    """
    def __init__(self, **kwargs):
        self._owner = None
        self._owner_permission = None
        self._owner_permission_auto_create = False
        self._owner_permission_help_text = None

        super(PermissionMixin, self).__init__(**kwargs)

    def Permission(self, permission=None, auto_create=False, help_text=None):
        if permission is None and not auto_create:
            raise ValueError('Please specify existion permission name or mark as auto_create=True')

        self._owner_permission = permission
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

    def __init__(self, **kwargs):
        task_title = kwargs.get('task_title', None)
        task_description = kwargs.get('task_description', None)
        view_or_cls = kwargs.get('view_or_cls', None)

        if task_title:
            self.task_title = task_title
        if task_description:
            self.task_description = task_description

        if view_or_cls:
            if view_or_cls.__doc__ and (self.task_title is None or self.task_description is None):
                docstring = view_or_cls.__doc__.split('\n\n', maxsplit=1)
                if task_title is None and len(docstring) > 0:
                    self.task_title = docstring[0].strip()
                if task_description is None and len(docstring) > 1:
                    self.task_description = docstring[1].strip()

        super(TaskDescriptionMixin, self).__init__(**kwargs)
