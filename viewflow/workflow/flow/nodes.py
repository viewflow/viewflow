from django.urls import path

from viewflow import viewprop, this
from viewflow.workflow import nodes
from . import views, mixins, utils


class Start(mixins.NodeDetailMixin, mixins.NodeUndoMixin, nodes.Start):
    """
    The ``Start`` node in a flow.

    This node is used as the initial step in a flow by a user.

    `Live Demo <https://demo.viewflow.io/workflow/flows/helloworld/start/>`_ /
    `Cookbook sample <https://github.com/viewflow/cookbook/blob/main/workflow101/helloworld/flows.py>`_

    .. code-block:: python

        class MyFlow(flow.Flow):
            start = (
                flow.Start(views.CreateProcessView.as_view(fields=["text"]))
                .Annotation(title=_("New message"))
                .Permission(auto_create=True)
                .Next(this.approve)
            )

            ...

    """

    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView

    @property
    def start_view(self):
        return this.resolve(self.flow_class.instance, self._start_view)

    @property
    def start_view_path(self):
        return path(
            f"{self.name}/",
            utils.wrap_start_view(self, self.start_view),
            name="execute",
        )


class StartHandle(mixins.NodeDetailMixin, mixins.NodeUndoMixin, nodes.StartHandle):
    """
    The ``Start`` handle node in a flow.

    This node is used as the initial step in a flow from code

    .. code-block:: python

        class MyFlow(flow.Flow):
            start = flow.StartHandle(this.on_start_process).Next(this.approve)

            def start_process(self, activation, sample=False):
                activation.process.sample = sample
                return activation.process

            ...

        process = MyFlow.start.run(sample=True)

    """

    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView


class End(
    mixins.NodeDetailMixin, mixins.NodeUndoMixin, mixins.NodeReviveMixin, nodes.End
):
    """
    The ``End`` node in a flow.

    This node serves as the terminal point of a flow

    .. code-block:: python

        class MyFlow(flow.Flow):
            ...

            approved = this.End()
            rejected = this.End()

    """

    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView


class View(
    mixins.NodeDetailMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    mixins.NodeReviveMixin,
    nodes.View,
):
    """
    Represents a user-interaction node within a flow

    .. code-block:: python

        class MyFlow(flow.Flow):
            ...

            approve = (
                flow.View(views.UpdateProcessView.as_view(fields=["approved"]))
                .Annotation(
                    title=_("Approve"),
                    description=_("Supervisor approvement"),
                    summary_template=_("Message review required"),
                    result_template=_(
                        "Message was {{ process.approved|yesno:'Approved,Rejected' }}"
                    ),
                )
                .Permission(auto_create=True)
                .Next(this.check_approve)
            )

            ...
    """

    index_view_class = views.UserIndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView

    """
    Execute View
    """

    @property
    def view(self):
        return this.resolve(self.flow_class.instance, self._view)

    @property
    def view_path(self):
        return path(
            f"<int:process_pk>/{self.name}/<int:task_pk>/execute/",
            utils.wrap_view(self, self.view),
            name="execute",
        )

    """
    Assign user to a task
    """
    assign_view_class = views.AssignTaskView

    @viewprop
    def assign_view(self):
        """View for a task assign."""
        if self.assign_view_class:
            return self.assign_view_class.as_view()

    @property
    def assign_path(self):
        if self.assign_view:
            return path(
                f"<int:process_pk>/{self.name}/<int:task_pk>/assign/",
                utils.wrap_task_view(
                    self, self.assign_view, permission=self.can_assign
                ),
                name="assign",
            )

    """
    Unassign
    """
    unassign_view_class = views.UnassignTaskView

    @viewprop
    def unassign_view(self):
        """View for a task assign."""
        if self.unassign_view_class:
            return self.unassign_view_class.as_view()

    @property
    def unassign_path(self):
        if self.unassign_view:
            return path(
                f"<int:process_pk>/{self.name}/<int:task_pk>/unassign/",
                utils.wrap_task_view(
                    self, self.unassign_view, permission=self.can_unassign
                ),
                name="unassign",
            )


class If(
    mixins.NodeDetailMixin, mixins.NodeUndoMixin, mixins.NodeReviveMixin, nodes.If
):
    """
    The  If-gate

    .. code-block:: python

        class MyFlow(flow.Flow):
            ...

            check_approve = (
                flow.If(lambda activation: activation.process.approved)
                .Annotation(title=_("Approvement check"))
                .Then(this.send)
                .Else(this.end)
            )

     .       ...
    """

    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView


class Function(mixins.NodeDetailMixin, mixins.NodeUndoMixin, nodes.Function):
    """
    Represents a callback function executed synchronously as part of a workflow
    node.

    A `Function` node is used within a flow to execute a callable (e.g., a
    method) that operates on the process instance. The execution is synchronous,
    meaning the workflow will wait for the callable to complete before
    proceeding to the next node.


    Usage:

    In the following example, a `Function` node is used within a `MyFlow` class
    to execute a logging function immediately after a task been activated.

    .. code-block:: python

        class MyFlow(flow.Flow):
            ...

            log_immediately = (
                flow.Function(this.log) .Next(this.end)
            )

            def log(self, activation):
                print(f"Process is in action {activation.process.pk}")


    """

    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView


class Handle(
    mixins.NodeDetailMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    mixins.NodeReviveMixin,
    nodes.Handle,
):
    """
    Represents a task executed from the other parts of code

    Usage:
    To define a handle in a flow and run it:

    .. code-block:: python

        class MyFlow(flow.Flow):
            ...
            my_handle = flow.Handle().Next(this.join_gate)

        task = task=process.task_set.get(flow_task=MyFlow.my_handle, status=STATUS.NEW),
        MyFlow.my_handle.run(task)
    """

    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView


class Obsolete(mixins.NodeDetailMixin, mixins.NodeCancelMixin, nodes.Obsolete):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView


class Join(
    mixins.NodeDetailMixin,
    mixins.NodeExecuteMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    mixins.NodeReviveMixin,
    nodes.Join,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView


class Split(
    mixins.NodeDetailMixin,
    mixins.NodeExecuteMixin,
    mixins.NodeUndoMixin,
    mixins.NodeReviveMixin,
    nodes.Split,
):
    """
    Represents a parallel split gateway in a workflow, allowing branching into multiple parallel paths.

    Methods:
        - `Next(node, case=None, data_source=None)`: Defines the subsequent node in the workflow.

          * `node`: The next node to execute.
          * `case` (optional): A callable that takes an activation and returns `True` if the node should be activated.
          * `data_source` (optional): A callable that takes an activation and returns a list of data items, creating an instance of the node for each item, with `task.data` set to the item.

        - `Always(node)`: A shortcut to define a subsequent node that is always executed.

    Example:

    .. code-block:: python

        flow.Split()
            .Next(
                this.approve,
                case=act.process.approved,
                data_source=lambda activation: [{"sample": "test task 1"}, {"sample": "test task 2"}],
            )
            .Always(this.required)


    In this example:
        - The `approve` node is executed multiple times based on the `data_source` list.
        - The `required` node is always executed unconditionally in parallel.

    Notes:
        - If `case` is not provided, the node is always activated.
        - If `data_source` is not provided, the node is created only once.
    """

    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView


class SplitFirst(
    mixins.NodeDetailMixin,
    nodes.SplitFirst,
):
    """
    Parallel split, as soon as the first task is completed, the remaining tasks
    are cancelled.

    The `SplitFirst` class is useful in workflows where you want to initiate
    multiple parallel tasks but only require the first task to complete,
    cancelling the rest once the first task finishes.

    Example:

    .. code-block:: python

        class MyFlow(flow.Flow):
            split_first = SplitFirst().Next(this.task_a).Next(this.task_b)

            task_a = flow.View(views.UserView).Next(this.join)

            task_b = celery.Timer(delay=timedelata(minutes=10)).Next(this.join)

            join = flow.Join()


    """

    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView


class StartSubprocess(
    mixins.NodeDetailMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    nodes.StartSubprocess,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView


class Subprocess(
    mixins.NodeDetailMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    nodes.Subprocess,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView


class NSubprocess(
    mixins.NodeDetailMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    nodes.NSubprocess,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView


class Switch(
    mixins.NodeDetailMixin,
    mixins.NodeCancelMixin,
    mixins.NodeUndoMixin,
    mixins.NodeReviveMixin,
    nodes.Switch,
):
    index_view_class = views.IndexTaskView
    detail_view_class = views.DetailTaskView
    cancel_view_class = views.CancelTaskView
    undo_view_class = views.UndoTaskView
    revive_view_class = views.ReviveTaskView
