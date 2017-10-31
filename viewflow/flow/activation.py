from ..activation import Activation, StartActivation, ViewActivation, STATUS
from ..exceptions import FlowRuntimeError


class ManagedStartViewActivation(StartActivation):
    """Tracks task statistics in activation form."""

    management_form_class = None

    def __init__(self, **kwargs):  # noqa D102
        super(ManagedStartViewActivation, self).__init__(**kwargs)
        self.management_form = None
        self.management_form_class = kwargs.pop('management_form_class', None)

    def get_management_form_class(self):
        """Activation management form class.

        Form used as intermediate storage before GET/POST task requests.
        """
        if self.management_form_class:
            return self.management_form_class
        else:
            return self.flow_class.management_form_class

    @Activation.status.super()
    def prepare(self, data=None, user=None):
        """Prepare activation for execution."""
        super(ManagedStartViewActivation, self).prepare.original()
        self.task.owner = user

        management_form_class = self.get_management_form_class()
        self.management_form = management_form_class(data=data, instance=self.task)

        if data:
            if not self.management_form.is_valid():
                raise FlowRuntimeError('Activation metadata is broken {}'.format(self.management_form.errors))
            self.task = self.management_form.save(commit=False)


class ManagedViewActivation(ViewActivation):
    """Tracks task statistics in activation form."""

    management_form_class = None

    def __init__(self, **kwargs):  # noqa D102
        super(ManagedViewActivation, self).__init__(**kwargs)
        self.management_form = None
        self.management_form_class = kwargs.pop('management_form_class', None)

    def get_management_form_class(self):
        """Activation management form class.

        Form used as intermediate storage before GET/POST task requests.
        """
        if self.management_form_class:
            return self.management_form_class
        else:
            return self.flow_class.management_form_class

    @Activation.status.super()
    def prepare(self, data=None, user=None):
        """Prepare activation for execution."""
        super(ManagedViewActivation, self).prepare.original()

        if user:
            self.task.owner = user

        management_form_class = self.get_management_form_class()
        self.management_form = management_form_class(data=data, instance=self.task)

        if data:
            if not self.management_form.is_valid():
                raise FlowRuntimeError('Activation metadata is broken {}'.format(self.management_form.errors))
            self.task = self.management_form.save(commit=False)

    @classmethod
    def create_task(cls, flow_task, prev_activation, token):
        """Create a task, calculate owner and permissions."""
        task = ViewActivation.create_task(flow_task, prev_activation, token)

        activation = task.activate()

        # Try to assign permission
        owner_permission = flow_task.calc_owner_permission(activation)
        if owner_permission:
            task.owner_permission = owner_permission

        # Try to assign owner
        owner = flow_task.calc_owner(activation)
        if owner:
            task.owner = owner
            task.status = STATUS.ASSIGNED

        return task
