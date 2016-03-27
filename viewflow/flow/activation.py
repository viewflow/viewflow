from ..activation import Activation, StartActivation, ViewActivation, STATUS
from ..exceptions import FlowRuntimeError


class ManagedStartViewActivation(StartActivation):
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
