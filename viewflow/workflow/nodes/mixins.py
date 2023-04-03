from viewflow import this

from ..activation import Activation
from ..status import STATUS
from ..base import Edge


class NextNodeActivationMixin(object):
    """Mixin for an activation of node with NextNodeMixin."""

    @Activation.status.transition(source=STATUS.DONE)
    def create_next(self):
        if self.flow_task._next:
            yield self.flow_task._next._create(self, self.task.token)


class NextNodeMixin(object):
    """Mixin for nodes that have only one outgoing path."""

    def __init__(self, *args, **kwargs):  # noqa D102
        self._next = None
        super().__init__(*args, **kwargs)

    def Next(self, node):
        """Next node to activate."""
        self._next = node
        return self

    def _resolve(self, cls):
        self._next = this.resolve(cls, self._next)

    def _outgoing(self):
        if self._next:
            yield Edge(src=self, dst=self._next, edge_class="next")


class NodePermissionMixin(object):
    """Node mixin to restrict access using django permissions."""

    _owner = None
    _owner_permission = None
    _owner_permission_auto_create = False
    _owner_permission_help_text = None

    def Permission(self, permission=None, auto_create=False, obj=None, help_text=None):
        """
        Make task available for users with specific permission.

        Accepts permissions name or callable :: Callable[Activation] -> string::

            .Permission('my_app.can_approve')
            .Permission(lambda process: 'my_app.department_manager_{}'.format(process.department.pk))

        Task specific permission could be auto created during migration::

            # Creates `process_class.can_do_task_process_class` permission
            do_task = View().Permission(auto_create=True)

            # You can specify permission codename and description right here
            # The following creates `process_class.can_execute_task` permission
            do_task = View().Permission('can_execute_task', help_text='Custom text', auto_create=True)
        """
        if permission is None and not auto_create:
            raise ValueError(
                "Please specify existing permission name or mark as auto_create=True"
            )

        self._owner_permission = permission
        self._owner_permission_obj = obj
        self._owner_permission_auto_create = auto_create
        self._owner_permission_help_text = help_text
        return self

    def _ready(self):
        """Insert additional flow permissions to the meta of the process model.

        Permissions itself are created as usual during django database
        migration process.
        """
        if self._owner_permission_auto_create:
            if self._owner_permission and "." in self._owner_permission:
                raise ValueError("Non qualified permission name expected")

            if not self._owner_permission:
                self._owner_permission = "can_{}_{}".format(
                    self.name, self.flow_class.process_class._meta.model_name
                )
                self._owner_permission_help_text = "Can {}".format(
                    self.name.replace("_", " ")
                )
            elif not self._owner_permission_help_text:
                self._owner_permission_help_text = self._owner_permission.replace(
                    "_", " "
                ).capitalize()

            for codename, _ in self.flow_class.process_class._meta.permissions:
                if codename == self._owner_permission:
                    break
            else:
                self.flow_class.process_class._meta.permissions = tuple(
                    self.flow_class.process_class._meta.permissions
                ) + ((self._owner_permission, self._owner_permission_help_text),)

            self._owner_permission = "{}.{}".format(
                self.flow_class.process_class._meta.app_label, self._owner_permission
            )
