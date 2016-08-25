from django.utils.timezone import now

from .. import Gateway, mixins, signals
from ..activation import Activation, STATUS, all_leading_canceled
from ..exceptions import FlowRuntimeError


class JoinActivation(Activation):
    def initialize(self, flow_task, task):
        self.flow_task, self.flow_class = flow_task, flow_task.flow_class

        self.process = self.flow_class.process_class._default_manager.get(flow_class=self.flow_class, pk=task.process_id)
        self.task = task

    def __init__(self, **kwargs):
        self.next_task = None
        super(JoinActivation, self).__init__(**kwargs)

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def start(self):
        self.task.save()
        signals.task_started.send(sender=self.flow_class, process=self.process, task=self.task)

    @Activation.status.transition(source=STATUS.STARTED)
    def done(self):
        with self.exception_guard():
            self.task.finished = now()
            self.set_status(STATUS.DONE)
            self.task.save()

            signals.task_finished.send(sender=self.flow_class, process=self.process, task=self.task)

            self.activate_next()

    def is_done(self):
        if not self.flow_task._wait_all:
            return True

        join_prefixes = set(
            prev.token.get_common_split_prefix(self.task.token, prev.pk)
            for prev in self.task.previous.exclude(status=STATUS.CANCELED).all())

        if len(join_prefixes) > 1:
            raise FlowRuntimeError('Multiple tokens {} cames to join {}'.format(join_prefixes, self.flow_task.name))

        join_token_prefix = next(iter(join_prefixes))

        active = self.flow_class.task_class._default_manager \
            .filter(process=self.process, token__startswith=join_token_prefix) \
            .exclude(status__in=[STATUS.DONE, STATUS.CANCELED])

        return not active.exists()

    @Activation.status.transition(source=STATUS.ERROR)
    def retry(self):
        if self.is_done():
            self.done.original()

    @Activation.status.transition(
        source=[STATUS.ERROR, STATUS.DONE],
        target=STATUS.STARTED,
        conditions=[all_leading_canceled])
    def undo(self):
        """
        Undo the task
        """
        super(JoinActivation, self).undo.original()

    @Activation.status.transition(source=[STATUS.NEW, STATUS.STARTED])
    def perform(self):
        if self.is_done():
            self.done.original()

    @Activation.status.transition(source=[STATUS.NEW, STATUS.STARTED], target=STATUS.CANCELED)
    def cancel(self):
        """
        Cancel existing task
        """
        super(JoinActivation, self).cancel.original()

    def activate_next(self):
        """
        Activate all outgoing edges
        """
        for outgoing in self.flow_task._outgoing():
            outgoing.dst.activate(prev_activation=self, token=self.task.token)

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
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

    task_type = 'JOIN'
    activation_class = JoinActivation

    def __init__(self, wait_all=True, **kwargs):
        super(Join, self).__init__(**kwargs)
        self._wait_all = wait_all
