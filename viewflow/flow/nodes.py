from .. import nodes
from . import views
from .activation import ManagedStartViewActivation, ManagedViewActivation


class StartFunction(nodes.StartFunction):
    """
    StartNode that can be executed within you code.

    Example::

        class MyFlow(Flow):
            start = flow.StartFunction(this.create_request)

            def create_request(self, activation, **kwargs):
                activation.prepare()
                activation.done()

        MyFlow.create_request.run(**kwargs)

    .. note::

        Any kwarg you pass of the run call will be passed to the function.

    """

    activate_next_view_class = views.ActivateNextTaskView
    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    perform_view_class = views.PerformTaskView
    undo_view_class = views.UndoTaskView


class Function(nodes.Function):
    """
    Node that can be executed within you code.

    Example::

        class MyFlow(Flow):
            my_task = flow.Function(this.perform_my_task)

            @method_decorator(flow.flow_func(task_loader=lambda flow_task, **kwargs: ... ))
            def perform_my_task(self, activation, **kwargs):
                activation.prepare()
                activation.done()

        MyFlow.my_task.run(**kwargs)

    .. note::

        Any kwarg you pass of the run call will be passed to the function.

    """

    activate_next_view_class = views.ActivateNextTaskView
    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    perform_view_class = views.PerformTaskView
    undo_view_class = views.UndoTaskView


class Handler(nodes.Handler):
    """
    Node that can be executed automatically after task was created.

    In difference to :class:`.Function` a :class:`.Handler` is not explicitly called
    in code, but executes automatically.

    Example::

        class MyFlow(Flow):
            my_task = (
                flow.Handler(this.handler_proc)
                .Next(this.End)
            )

            def my_handler(self. activation):
                # Your custom code
                pass

    .. note::

        You don't need to call ``prepare()`` or ``done()`` on the
        activation in you handler callback.

    """

    activate_next_view_class = views.ActivateNextTaskView
    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    perform_view_class = views.PerformTaskView
    undo_view_class = views.UndoTaskView


class If(nodes.If):
    """
    Activates one of paths based on condition.

    Example::

        class MyFlow(Flow):
            check_approve = (
                flow.If(lambda activation: activation.process.is_approved)
                .Then(this.send_message)
                .Else(this.end_rejected)
            )
    """

    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    perform_view_class = views.PerformTaskView
    undo_view_class = views.UndoTaskView


class Switch(nodes.Switch):
    """Activates first path with matched condition."""

    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    perform_view_class = views.PerformTaskView
    undo_view_class = views.UndoTaskView


class Join(nodes.Join):
    """
    Waits for one or all incoming links and activates next path.

    Join should be connected to one split task only.

    Example::

        join_on_warehouse = flow.Join().Next(this.next_task)

    """

    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    perform_view_class = views.PerformTaskView
    undo_view_class = views.UndoTaskView


class Split(nodes.Split):
    """
    Activates outgoing path in-parallel depends on per-path condition.

    Example::

        split_on_decision = (
            flow.Split()
            .Next(check_post, cond=lambda p: p,is_check_post_required)
            .Next(this.perform_task_always)
        )
    """

    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    perform_view_class = views.PerformTaskView
    undo_view_class = views.UndoTaskView


class AbstractJob(nodes.AbstractJob):
    """Base task for background jobs."""

    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    perform_view_class = views.PerformTaskView
    undo_view_class = views.UndoTaskView


class StartSignal(nodes.StartSignal):
    """
    StartNode that connects to a django signal.

    Example::

        def my_start_receiver(activation, **signal_kwargs):
            activation.prepare()
            # You custom code
            activation.done()

        class MyFlow(Flow):
            start = flow.StartSignal(post_save, my_start_receiver, sender=MyModelCls)

    .. note::

        The first argument of your receiver will be the activation.

    """

    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView


class Signal(nodes.Signal):
    """
    Node that connects to a django signal.

    Example::

        create_model = flow.Signal(post_create, my_receiver, sender=MyModelCls)

    .. note::

        Other than the :class:`.StartSignal` you will need to provide activation
        for your receiver yourself. This can be done using the :func:`.flow_signal`
        decorator.

    """

    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView


class Start(nodes.Start):
    """
    Start process event.

    Example::

        start = (
            flow.Start(StartView, fields=["some_process_field"])
            .Available(lambda user: user.is_super_user)
            .Next(this.next_task)
        )

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

    activate_next_view_class = views.ActivateNextTaskView
    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView
    start_view_class = views.CreateProcessView

    activation_class = ManagedStartViewActivation


class View(nodes.View):
    """
    View task.

    Example::

        task = (
            flow.View(some_view)
                .Permission('my_app.can_do_task')
                .Next(this.next_task)
        )

    In case of function based view::

        task = flow.Task(task)

        @flow_start_view()
        def task(request, activation):
             if not activation.flow_task.has_perm(request.user):
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

    activate_next_view_class = views.ActivateNextTaskView
    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    undo_view_class = views.UndoTaskView
    assign_view_class = views.AssignTaskView
    unassign_view_class = views.UnassignTaskView

    activation_class = ManagedViewActivation


class End(nodes.End):
    """End process event."""

    cancel_view_class = views.CancelTaskView
    detail_view_class = views.DetailTaskView
    perform_view_class = views.PerformTaskView
    undo_view_class = views.UndoTaskView
