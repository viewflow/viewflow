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

    def __init__(self, activation_cls=None):
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
        self._assign_view = None

        super(PermissionMixin, self).__init__(**kwargs)

    def Permission(self, permission=None, assign_view=None, auto_create=False, help_text=None):
        """
        Make process start available for users with specific permission.
        For existing permission accepts permissions name or callable predicate :: User -> bool::

            .Permission('processmodel.can_approve')
            .Permission(lambda user: user.department_id is not None)

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
        self._owner_permission_auto_create = auto_create
        self._owner_permission_help_text = help_text
        self._assign_view = assign_view

        return self

    def ready(self):
        if self._owner_permission_auto_create:
            if self._owner_permission and '.' in self._owner_permission:
                raise ValueError('Non qualified permission name expected')

            if not self._owner_permission:
                self._owner_permission = 'can_{}_{}'.format(self.name, self.flow_cls.process_cls._meta.model_name)
            if not self._owner_permission_help_text:
                self._owner_permission_help_text = self._owner_permission.replace('_', ' ').capitalize()

            for codename, _ in self.flow_cls.process_cls._meta.permissions:
                if codename == self._owner_permission:
                    break
            else:
                self.flow_cls.process_cls._meta.permissions.append(
                    (self._owner_permission, self._owner_permission_help_text))

            self._owner_permission = '{}.{}'.format(self.flow_cls.process_cls._meta.app_label, self._owner_permission)
