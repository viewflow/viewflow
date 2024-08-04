from django.utils.timezone import now

from viewflow import this
from viewflow.utils import is_owner
from ..base import Node
from ..activation import Activation, leading_tasks_canceled, has_manage_permission
from ..status import STATUS, PROCESS
from ..signals import task_started, task_finished, flow_started
from . import mixins


class StartActivation(mixins.NextNodeActivationMixin, Activation):
    """Task activation that creates new process instance."""

    @classmethod
    def create(cls, flow_task, prev_activation, token, data=None, seed=None):
        flow_class = flow_task.flow_class

        process = flow_class.process_class(flow_class=flow_class)
        task = flow_class.task_class(
            flow_task=flow_task,
            process=process,
            started=now(),
        )
        task.data = data if data is not None else {}
        task.seed = seed
        return cls(task)

    @Activation.status.transition(source=STATUS.NEW)
    def execute(self):
        task_started.send(sender=self.flow_class, process=self.process, task=self.task)
        self.process.save()
        with self.flow_class.lock(self.process.pk):
            self.complete()
            flow_started.send(
                sender=self.flow_class,
                process=self.process,
                task=self.task,
            )
            self.activate_next()


class StartHandleActivation(StartActivation):
    @Activation.status.transition(
        source=STATUS.DONE,
        target=STATUS.CANCELED,
        conditions=[leading_tasks_canceled],
        permission=has_manage_permission,
    )
    def undo(self):
        # undo
        if self.flow_task._undo_func is not None:
            self.flow_task._undo_func(self)

        # cancel process
        self.process.finished = now()
        self.process.status = PROCESS.CANCELED
        self.process.save()

        # finish task
        self.task.finished = now()
        self.task.save()


class StartViewActivation(StartActivation):
    """Task activation that creates new process instance."""

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def start(self, request):
        self.task.owner = request.user

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.DONE)
    def complete(self):
        super().complete.original()

    @Activation.status.transition(source=STATUS.STARTED)
    def execute(self):
        super().execute.original()

    @Activation.status.super()
    def undo(self):
        # undo
        if self.flow_task._undo_func is not None:
            self.flow_task._undo_func(self)

        # cancel process
        self.process.finished = now()
        self.process.status = PROCESS.CANCELED
        self.process.save()

        super().undo.original()

    def get_success_url(self, request):
        return request.resolver_match.flow_viewset.get_success_url(request)


class Start(
    mixins.NextNodeMixin,
    mixins.NodePermissionMixin,
    Node,
):
    """Start a flow from django view."""

    activation_class = StartViewActivation

    task_type = "HUMAN_START"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event" cx="25" cy="25" r="25"/>
        """,
    }

    bpmn_element = "startEvent"

    def __init__(self, view, undo_func=None, **kwargs):
        super().__init__()
        self._task_result_summary = "Process launched"
        self._start_view = view
        self._undo_func = undo_func

    def can_execute(self, user, task=None):
        """
        Check whether the user is authorized to start a flow.

        This method checks whether the user is authorized to start a flow based on the
        owner and owner permission attributes.
        """
        if not user.is_authenticated:
            return False

        if task and task.status != STATUS.NEW:
            return False

        from django.contrib.auth import get_user_model

        if self._owner:
            if callable(self._owner):
                return self._owner(user)
            else:
                owner = get_user_model()._default_manager.get(**self._owner)
                return is_owner(owner, user)

        elif self._owner_permission:
            obj = None
            if self._owner_permission_obj:
                if callable(self._owner_permission_obj):
                    obj = self._owner_permission_obj()
                else:
                    obj = self._owner_permission_obj

            return user.has_perm(self._owner_permission, obj=obj) or user.has_perm(
                self._owner_permission
            )

        else:
            """
            No restriction
            """
            return True


class StartHandle(mixins.NextNodeMixin, Node):
    """Start flow from code."""

    task_type = "START"

    shape = {
        "width": 50,
        "height": 50,
        "svg": """
            <circle class="event" cx="25" cy="25" r="25"/>
            <rect xmlns="http://www.w3.org/2000/svg" x="7.5" y="15" width="35" height="20" fill="transparent" stroke="rgb(0, 0, 0)"/>
            <path xmlns="http://www.w3.org/2000/svg" d="M 7.5 15 L 25 25 L 42.5 15" fill="none" stroke="rgb(0, 0, 0)" stroke-miterlimit="10"/>
        """,
    }

    bpmn_element = "startEvent"

    activation_class = StartHandleActivation

    def __init__(self, func=None, undo_func=None):
        super().__init__()
        self._func = func
        self._undo_func = undo_func

    def _create_wrapper_function(self, origin_func):
        def func(**kwargs):
            activation = self.activation_class.create(self, None, None)

            # link subprocess to a parent process
            activation.process.parent_task = kwargs.pop("_parent_task", None)
            activation.process.data = kwargs.pop("_process_data", {})
            activation.process.seed = kwargs.pop("_process_seed", None)
            activation.task.data = kwargs.pop("_task_data", {})
            activation.task.seed = kwargs.pop("_task_seed", None)

            result = (
                origin_func(activation, **kwargs) if origin_func else activation.process
            )
            activation.execute()
            return result

        return func

    def run(self, **kwargs):
        func = this.resolve(self.flow_class.instance, self._func)
        wrapper = self._create_wrapper_function(func)
        return wrapper(**kwargs)
