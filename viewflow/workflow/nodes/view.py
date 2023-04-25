from django.utils.timezone import now

from viewflow import this
from viewflow.utils import is_owner
from ..base import Node
from ..activation import Activation, has_manage_permission
from ..status import STATUS
from ..signals import task_started, task_finished
from . import mixins


class ViewActivation(mixins.NextNodeActivationMixin, Activation):
    """View node activation."""

    @classmethod
    def create(cls, flow_task, prev_activation, token):
        """Instantiate and persist new flow task."""
        flow_class = flow_task.flow_class
        task = flow_class.task_class(
            process=prev_activation.process, flow_task=flow_task, token=token
        )

        activation = cls(task)

        # Try to assign permission
        owner_permission = flow_task.calc_owner_permission(activation)
        if owner_permission:
            task.owner_permission = owner_permission
            task.owner_permission_obj = flow_task.calc_owner_permission_obj(activation)

        # Try to assign owner
        owner = flow_task.calc_owner(activation)
        if owner:
            task.owner = owner
            task.status = STATUS.ASSIGNED

        task.save()
        task.previous.add(prev_activation.task)

        if flow_task._on_create is not None:
            flow_task._on_create(activation)

        return activation

    @Activation.status.transition(
        source=STATUS.NEW,
        target=STATUS.ASSIGNED,
        permission=lambda activation, user: activation.flow_task.can_assign(
            user, activation.task
        ),
    )
    def assign(self, user):
        """Assign user to the task."""
        self.task.owner = user
        self.task.save()

    @Activation.status.transition(
        source=STATUS.ASSIGNED,
        target=STATUS.NEW,
        permission=lambda activation, user: activation.flow_task.can_unassign(
            user, activation.task
        ),
    )
    def unassign(self):
        """Remove user from the task assignment."""
        self.task.owner = None
        self.task.save()

    @Activation.status.transition(
        source=STATUS.ASSIGNED,
        permission=lambda activation, user: activation.flow_task.can_unassign(
            user, activation.task
        ),
    )
    def reassign(self, user=None):
        """Reassign to another user."""
        if user:
            self.task.owner = user
        self.task.save()

    @Activation.status.super()
    def activate(self):
        """Do nothing on sync call"""

    @Activation.status.transition(
        label="Execute",
        source=STATUS.ASSIGNED,
        target=STATUS.STARTED,
        permission=lambda activation, user: activation.flow_task.can_execute(
            user, activation.task
        ),
    )
    def start(self, request):
        # TODO request.GET['started']
        task_started.send(sender=self.flow_class, process=self.process, task=self.task)
        self.task.started = now()

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.DONE)
    def complete(self):
        """Complete task and create next."""
        super().complete.original()

    @Activation.status.transition(
        source=STATUS.STARTED,
        permission=lambda activation, user: activation.flow_task.can_execute(
            user, activation.task
        ),
    )
    def execute(self):
        self.complete()
        task_finished.send(sender=self.flow_class, process=self.process, task=self.task)
        self.activate_next()

    @Activation.status.transition(
        source=[STATUS.NEW, STATUS.ASSIGNED],
        target=STATUS.CANCELED,
        permission=has_manage_permission,
    )
    def cancel(self):
        self.task.finished = now()
        self.task.save()

    @Activation.status.super()
    def undo(self):
        # undo
        if self.flow_task._undo_func is not None:
            self.flow_task._undo_func(self)

        super().undo.original()


class View(
    mixins.NextNodeMixin,
    mixins.NodePermissionMixin,
    Node,
):
    """User task."""

    activation_class = ViewActivation

    task_type = "HUMAN"

    shape = {
        "width": 150,
        "height": 100,
        "text-align": "middle",
        "svg": """
            <rect class="task" width="150" height="100" rx="5" ry="5"/>
        """,
    }

    bpmn_element = "userTask"

    def __init__(self, view, undo_func=None, **kwargs):
        super().__init__()
        self._view = view
        self._undo_func = undo_func
        self._on_create = None

    def _resolve(self, instance):
        super()._resolve(instance)
        self._on_create = this.resolve(instance, self._on_create)

    """
    Task assign permissions
    """

    def Assign(self, owner=None, **owner_kwargs):
        """
        Assign task to the User immediately on activation.

        Accepts user lookup kwargs or callable :: Process -> User::

            .Assign(username='employee')
            .Assign(lambda activation: activation.process.created_by)
        """
        if owner:
            self._owner = owner
        else:
            self._owner = owner_kwargs
        return self

    def onCreate(self, ref):
        """
        Call a function when task created::

            class MyFlow(Flow):
                approve = flow.View(...).OnCreate(this.on_approve_created)

                def on_approve_created(self, activation):
                    if activation.task.owner:
                        send_mail(
                            'View task assigned to you','Here is the message.',
                            'from@example.com', [activation.task.owner.email]
                        )
        """
        self._on_create = ref
        return self

    def calc_owner(self, activation):
        """Determine a user to auto-assign the task."""
        from django.contrib.auth import get_user_model

        owner = this.resolve(self.flow_class.instance, self._owner)
        if callable(owner):
            owner = owner(activation)
        elif isinstance(owner, dict):
            owner = get_user_model()._default_manager.get(**owner)
        return owner

    def calc_owner_permission(self, activation):
        """Determine required permission to assign and execute this task."""
        owner_permission = self._owner_permission
        if callable(owner_permission):
            owner_permission = owner_permission(activation)
        return owner_permission

    def calc_owner_permission_obj(self, activation):
        """Determine required permission to assign and execute this task."""
        if self._owner_permission_obj:
            return self._owner_permission_obj(activation.process)

    def can_execute(self, user, task):
        """Check user permission to execute the task."""
        return is_owner(task.owner, user)

    def can_assign(self, user, task):
        """Check if user can assign the task."""
        # already assigned
        if task.owner_id:
            return False

        # user not logged in
        if user is None or user.is_anonymous:
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

        return user.has_perm(task.owner_permission, obj=obj) or user.has_perm(
            task.owner_permission
        )

    def can_unassign(self, user, task):
        """Check if user can unassign the task."""
        # not assigned
        if task.owner_id is None:
            return False

        # user not logged in
        if user is None or user.is_anonymous:
            return False

        # Assigned to the same user
        if is_owner(task.owner, user):
            return True

        # User have flow management permissions
        return self.flow_class.instance.has_manage_permission(user)

    """
    TODO: Reassign
    """
