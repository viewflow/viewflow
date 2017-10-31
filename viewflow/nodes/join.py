from django.utils.timezone import now

from .. import Gateway, mixins, signals
from ..activation import Activation, STATUS, all_leading_canceled
from ..exceptions import FlowRuntimeError


class JoinActivation(Activation):
    """Activation for parallel Join node."""

    def __init__(self, **kwargs):  # noqa D102
        self.next_task = None
        super(JoinActivation, self).__init__(**kwargs)

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def start(self):
        """Create Join task on the first incoming node complete."""
        self.task.save()
        signals.task_started.send(sender=self.flow_class, process=self.process, task=self.task)

    @Activation.status.transition(source=STATUS.STARTED)
    def done(self):
        """Complete the join within current exception propagation strategy."""
        with self.exception_guard():
            self.task.finished = now()
            self.set_status(STATUS.DONE)
            self.task.save()

            signals.task_finished.send(sender=self.flow_class, process=self.process, task=self.task)

            self.activate_next()

    def is_done(self):
        """Check that process can be continued futher.

        Join check the all task state in db with the common token prefix.

        Join node would continue execution if all incoming tasks are DONE or CANCELED.
        """
        if not self.flow_task._wait_all:
            return True

        join_prefixes = set(
            prev.token.get_common_split_prefix(self.task.token, prev.pk)
            for prev in self.task.previous.exclude(status=STATUS.CANCELED).all())

        if len(join_prefixes) > 1:
            raise FlowRuntimeError('Multiple tokens {} came to join {}'.format(join_prefixes, self.flow_task.name))

        join_token_prefix = next(iter(join_prefixes))

        active = self.flow_class.task_class._default_manager \
            .filter(process=self.process, token__startswith=join_token_prefix) \
            .exclude(status__in=[STATUS.DONE, STATUS.CANCELED])

        return not active.exists()

    @Activation.status.transition(source=STATUS.ERROR)
    def retry(self):
        """Manual join gateway reactivation after an error."""
        if self.is_done():
            self.done.original()

    @Activation.status.transition(
        source=[STATUS.ERROR, STATUS.DONE],
        target=STATUS.STARTED,
        conditions=[all_leading_canceled])
    def undo(self):
        """Undo the task."""
        super(JoinActivation, self).undo.original()

    @Activation.status.transition(source=[STATUS.NEW, STATUS.STARTED])
    def perform(self):
        """Manual gateway activation."""
        if self.is_done():
            self.done.original()

    @Activation.status.transition(source=[STATUS.NEW, STATUS.STARTED], target=STATUS.CANCELED)
    def cancel(self):
        """Cancel existing join."""
        super(JoinActivation, self).cancel.original()

    @Activation.status.transition(source=STATUS.DONE)
    def activate_next(self):
        """Activate all outgoing edges."""
        for outgoing in self.flow_task._outgoing():
            outgoing.dst.activate(prev_activation=self, token=self.task.token)

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        """Join and if all incoming path completed, continue execution.

        Join task is created on the first activation. Subsequent
        activations would lookup for the Join Task instance.

        """
        flow_class, flow_task = flow_task.flow_class, flow_task
        process = prev_activation.process

        # lookup for active join instance
        tasks = flow_class.task_class._default_manager.filter(
            flow_task=flow_task,
            process=process,
            status=STATUS.STARTED)

        if len(tasks) > 1:
            raise FlowRuntimeError('More than one join instance for process found')

        activation = cls()

        task = tasks.first()
        if not task:
            if token.is_split_token():
                token = token.get_base_split_token()

            task = flow_class.task_class(
                process=process,
                flow_task=flow_task,
                token=token)

            task.save()
            task.previous.add(prev_activation.task)

            activation.initialize(flow_task, task)
            activation.start()
        else:
            task.previous.add(prev_activation.task)
            activation.initialize(flow_task, task)

        if activation.is_done():
            activation.done()

        return activation


class Join(mixins.TaskDescriptionMixin,
           mixins.NextNodeMixin,
           mixins.DetailViewMixin,
           mixins.UndoViewMixin,
           mixins.CancelViewMixin,
           mixins.PerformViewMixin,
           Gateway):
    """Wait for one or all incoming links and activates next path.

    Without a Join, subsequent task would be activated as many times
    as it have parallel incoming links.

    Example::

        class MyFlow(Flow):
            prepare_item = (
                flow.Split()
                .Next(this.make_box)
                .Next(this.make_label)
            )

            make_box = (
                flow.View(ConfirmView, fields=['box_done'])
                .Next(this.item_prepared)
            )

            make_label = (
                flow.View(ConfirmView, fields=['label_done'])
                .Next(this.item_prepared)
            )

            item_prepared = flow.Join().Next(this.end)

    """

    task_type = 'JOIN'
    activation_class = JoinActivation

    def __init__(self, wait_all=True, **kwargs):  # noqa D102
        super(Join, self).__init__(**kwargs)
        self._wait_all = wait_all
