from django.utils.timezone import now

from .. import signals
from ..activation import all_leading_canceled, Activation, AbstractGateActivation, STATUS
from ..exceptions import FlowRuntimeError
from ..token import Token
from . import base


class IfActivation(AbstractGateActivation):
    def __init__(self, **kwargs):
        self.condition_result = None
        super(IfActivation, self).__init__(**kwargs)

    def calculate_next(self):
        self.condition_result = self.flow_task.condition(self.process)

    def activate_next(self):
        if self.condition_result:
            self.flow_task._on_true.activate(prev_activation=self, token=self.task.token)
        else:
            self.flow_task._on_false.activate(prev_activation=self, token=self.task.token)


class If(base.TaskDescriptionMixin,
         base.DetailsViewMixin,
         base.UndoViewMixin,
         base.CancelViewMixin,
         base.PerformViewMixin,
         base.Gateway):
    """
    Activates one of paths based on condition

    Example::

       check_decision = flow.If(lambda p: p.approved) \\
           .OnTrue(this.approved) \\
           .OnFalse(this.end)
    """
    task_type = 'IF'
    activation_cls = IfActivation

    def __init__(self, cond, **kwargs):
        super(If, self).__init__(**kwargs)
        self._condition = cond
        self._on_true = None
        self._on_false = None

    def _outgoing(self):
        yield base.Edge(src=self, dst=self._on_true, edge_class='cond_true')
        yield base.Edge(src=self, dst=self._on_false, edge_class='cond_false')

    def _resolve(self, resolver):
        self._on_true = resolver.get_implementation(self._on_true)
        self._on_false = resolver.get_implementation(self._on_false)

    def OnTrue(self, node):
        self._on_true = node
        return self

    def OnFalse(self, node):
        self._on_false = node
        return self

    @property
    def condition(self):
        return self._condition


class SwitchActivation(AbstractGateActivation):
    def __init__(self, **kwargs):
        self.next_task = None
        super(SwitchActivation, self).__init__(**kwargs)

    def calculate_next(self):
        for node, cond in self.flow_task.branches:
            if cond:
                if cond(self.process):
                    self.next_task = node
                    break
            else:
                self.next_task = node

        if not self.next_task:
            raise FlowRuntimeError('No next task available for {}'.format(self.flow_task.name))

    def activate_next(self):
        self.next_task.activate(prev_activation=self, token=self.task.token)


class Switch(base.TaskDescriptionMixin,
             base.DetailsViewMixin,
             base.UndoViewMixin,
             base.CancelViewMixin,
             base.PerformViewMixin,
             base.Gateway):
    """
    Activates first path with matched condition
    """
    task_type = 'SWITCH'
    activation_cls = SwitchActivation

    def __init__(self, **kwargs):
        super(Switch, self).__init__(**kwargs)
        self._activate_next = []

    def _outgoing(self):
        for next_node, cond in self._activate_next:
            edge_class = 'cond_true' if cond else 'default'
            yield base.Edge(src=self, dst=next_node, edge_class=edge_class)

    def _resolve(self, resolver):
        self._activate_next = \
            [(resolver.get_implementation(node), cond)
             for node, cond in self._activate_next]

    @property
    def branches(self):
        return self._activate_next

    def Case(self, node, cond=None):
        self._activate_next.append((node, cond))
        return self

    def Default(self, node):
        self._activate_next.append((node, None))
        return self


class JoinActivation(Activation):
    def initialize(self, flow_task, task):
        self.flow_task, self.flow_cls = flow_task, flow_task.flow_cls

        self.process = self.flow_cls.process_cls._default_manager.get(flow_cls=self.flow_cls, pk=task.process_id)
        self.task = task

    def __init__(self, **kwargs):
        self.next_task = None
        super(JoinActivation, self).__init__(**kwargs)

    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def start(self):
        self.task.save()
        signals.task_started.send(sender=self.flow_cls, process=self.process, task=self.task)

    @Activation.status.transition(source=STATUS.STARTED)
    def done(self):
        with self.exception_guard():
            self.task.finished = now()
            self.set_status(STATUS.DONE)
            self.task.save()

            signals.task_finished.send(sender=self.flow_cls, process=self.process, task=self.task)

            self.activate_next()

    def is_done(self):
        if not self.flow_task._wait_all:
            return True

        join_prefixes = set(
            prev.token.get_common_split_prefix()
            for prev in self.task.previous.exclude(status=STATUS.CANCELED).all())

        if len(join_prefixes) > 1:
            raise FlowRuntimeError('Multiple tokens {} cames to join {}'.format(join_prefixes, self.flow_task.name))

        join_token_prefix = next(iter(join_prefixes))

        active = self.flow_cls.task_cls._default_manager \
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
        flow_cls, flow_task = flow_task.flow_cls, flow_task
        process = prev_activation.process

        # lookup for active join instance
        tasks = flow_cls.task_cls._default_manager.filter(
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

            task = flow_cls.task_cls(
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


class Join(base.TaskDescriptionMixin,
           base.NextNodeMixin,
           base.DetailsViewMixin,
           base.UndoViewMixin,
           base.CancelViewMixin,
           base.PerformViewMixin,
           base.Gateway):
    """
    Waits for one or all incoming links and activates next path.

    Join should be connected to one split task only.

    Example::

        join_on_warehouse = flow.Join() \\
            .Next(this.next_task)

    """
    task_type = 'JOIN'
    activation_cls = JoinActivation

    def __init__(self, wait_all=True, **kwargs):
        super(Join, self).__init__(**kwargs)
        self._wait_all = wait_all


class SplitActivation(AbstractGateActivation):
    def __init__(self, **kwargs):
        self.next_tasks = []
        super(SplitActivation, self).__init__(**kwargs)

    def calculate_next(self):
        for node, cond in self.flow_task.branches:
            if cond:
                if cond(self.process):
                    self.next_tasks.append(node)
            else:
                self.next_tasks.append(node)

        if not self.next_tasks:
            raise FlowRuntimeError('No next task available for {}'.format(self.flow_task.name))

    def activate_next(self):
        token_source = Token.split_token_source(self.task.token, self.task.pk)

        for n, next_task in enumerate(self.next_tasks, 1):
            next_task.activate(prev_activation=self, token=next(token_source))


class Split(base.TaskDescriptionMixin,
            base.DetailsViewMixin,
            base.UndoViewMixin,
            base.CancelViewMixin,
            base.PerformViewMixin,
            base.Gateway):
    """
    Activates outgoing path in-parallel depends on per-path condition.

    Example::

        split_on_decision = flow.Split() \\
            .Next(check_post, cond=lambda p: p,is_check_post_required) \\
            .Next(this.perform_task_always)
    """
    task_type = 'SPLIT'
    activation_cls = SplitActivation

    def __init__(self, **kwargs):
        super(Split, self).__init__(**kwargs)
        self._activate_next = []

    def _outgoing(self):
        for next_node, cond in self._activate_next:
            edge_class = 'cond_true' if cond else 'default'
            yield base.Edge(src=self, dst=next_node, edge_class=edge_class)

    def _resolve(self, resolver):
        self._activate_next = \
            [(resolver.get_implementation(node), cond)
             for node, cond in self._activate_next]

    @property
    def branches(self):
        return self._activate_next

    def Next(self, node, cond=None):
        self._activate_next.append((node, cond))
        return self

    def Always(self, node):
        self._activate_next.append((node, None))
        return self


class First(base.DetailsViewMixin, base.Gateway):
    """
    TODO: Wait for first of outgoing task to be completed and cancels all others
    """
    task_type = 'FIRST_OF'

    def __init__(self, **kwargs):
        super(First, self).__init__(**kwargs)
        self._activate_list = []

    def _outgoing(self):
        for next_node in self._activate_list:
            yield base.Edge(src=self, dst=next_node, edge_class='next')

    def _resolve(self, resolver):
        self._activate_list = \
            [resolver.get_implementation(node) for node in self._activate_list]

    def Of(self, node):
        self._activate_list.append(node)
        return self

    def activate(self, prev_activation):
        pass  # TODO
