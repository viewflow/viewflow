from viewflow.activation import Activation, GateActivation
from viewflow.exceptions import FlowRuntimeError
from viewflow.flow.base import Gateway, Edge


class IfActivation(GateActivation):
    def __init__(self, **kwargs):
        self.condition_result = None
        super(IfActivation, self).__init__(**kwargs)

    def execute(self):
        self.condition_result = self.flow_task.condition(self)


class If(Gateway):
    """
    Activates one of paths based on condition
    """
    task_type = 'IF'
    activation_cls = IfActivation

    def __init__(self, cond):
        super(If, self).__init__()
        self._condition = cond
        self._on_true = None
        self._on_false = None

    def _outgoing(self):
        yield Edge(src=self, dst=self._on_true, edge_class='cond_true')
        yield Edge(src=self, dst=self._on_false, edge_class='cond_false')

    def OnTrue(self, node):
        self._on_true = node
        return self

    def OnFalse(self, node):
        self._on_false = node
        return self

    @property
    def condition(self):
        return self._condition

    def activate_next(self, self_activation, **kwargs):
        if self_activation.condition_result:
            self._on_true.activate(self_activation, self_activation.task.token)
        else:
            self._on_false.activate(self_activation, self_activation.task.token)


class SwitchActivation(GateActivation):
    def __init__(self, **kwargs):
        self.next_task = None
        super(SwitchActivation, self).__init__(**kwargs)

    def execute(self):
        for node, cond in self.flow_task.branches:
            if cond:
                if cond():
                    self.next_task = node
                    break
            else:
                self.next_task = node

        if not self.next_task:
            raise FlowRuntimeError('No next task available for {}'.format(self.flow_task.name))


class Switch(Gateway):
    """
    Activates first path with matched condition
    """
    task_type = 'SWITCH'
    activation_cls = SwitchActivation

    def __init__(self):
        super(Switch, self).__init__()
        self._activate_next = []

    def _outgoing(self):
        for next_node, cond in self._activate_next:
            edge_class = 'cond_true' if cond else 'default'
            yield Edge(src=self, dst=next_node, edge_class=edge_class)

    @property
    def branches(self):
        return self._activate_next

    def Case(self, node, cond=None):
        self._activate_next.append((node, cond))
        return self

    def Default(self, node):
        self._activate_next.append((node, None))
        return self

    def activate_next(self, self_activation, **kwargs):
        self_activation.next_task.activate(self_activation, self_activation.task.token)


class JoinActivation(Activation):
    def initialize(self, flow_task, task):
        self.flow_task, self.flow_cls = flow_task, flow_task.flow_cls

        self.process = self.flow_cls.process_cls._default_manager.get(flow_cls=self.flow_cls, pk=task.process_id)
        self.task = task

    def __init__(self, **kwargs):
        self.next_task = None
        super(JoinActivation, self).__init__(**kwargs)

    def prepare(self):
        self.task.prepare()

    def start(self):
        self.task.start()
        self.task.save()

    def done(self):
        self.task.done()
        self.task.save()

        self.flow_task.activate_next(self)

    def is_done(self):
        if not self.flow_task._wait_all:
            return True

        all_links = set(x.src for x in self.flow_task._incoming())
        finished_links = set(task.flow_task for task in self.task.previous.all())
        return finished_links == all_links

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        flow_cls, flow_task = flow_task.flow_cls, flow_task
        process = prev_activation.process

        # lookup for active join instance
        tasks = flow_cls.task_cls._default_manager.filter(
            flow_task=flow_task,
            process=process,
            status=flow_cls.task_cls.STATUS.STARTED)

        if len(tasks) > 1:
            raise FlowRuntimeError('More than one join instance for process found')

        activation = cls()

        task = tasks.first()
        if not task:
            task = flow_cls.task_cls(
                process=process,
                flow_task=flow_task,
                token=token)

            task.save()
            task.previous.add(prev_activation.task)
            activation.initialize(flow_task, task)
            activation.prepare()
            activation.start()
        else:
            activation.initialize(flow_task, task)

        if activation.is_done():
            activation.done()

        return activation


class Join(Gateway):
    """
    Wait for one or all incoming links and activate next path
    """
    task_type = 'JOIN'
    activation_cls = JoinActivation

    def __init__(self, wait_all=True):
        super(Join, self).__init__()
        self._wait_all = wait_all
        self._activate_next = []

    def _outgoing(self):
        for next_node in self._activate_next:
            yield Edge(src=self, dst=next_node, edge_class='next')

    def Next(self, node):
        self._activate_next.append(node)
        return self

    def activate_next(self, self_activation, **kwargs):
        """
        Activate all outgoing edges
        """
        for outgoing in self._outgoing():
            outgoing.dst.activate(prev_activation=self_activation,
                                  token=self_activation.task.token)


class SplitActivation(GateActivation):
    def __init__(self, **kwargs):
        self.next_tasks = []
        super(SplitActivation, self).__init__(**kwargs)

    def execute(self):
        for node, cond in self.flow_task.branches:
            if cond:
                if cond(self):
                    self.next_tasks.append(node)
            else:
                self.next_tasks.append(node)

        if not self.next_tasks:
            raise FlowRuntimeError('No next task available for {}'.format(self.flow_task.name))


class Split(Gateway):
    """
    Activate outgoing path in-parallel depends on per-path condition
    """
    task_type = 'SPLIT'
    activation_cls = SplitActivation

    def __init__(self):
        super(Split, self).__init__()
        self._activate_next = []

    def _outgoing(self):
        for next_node, cond in self._activate_next:
            edge_class = 'cond_true' if cond else 'default'
            yield Edge(src=self, dst=next_node, edge_class=edge_class)

    @property
    def branches(self):
        return self._activate_next

    def Next(self, node, cond=None):
        self._activate_next.append((node, cond))
        return self

    def Always(self, node):
        self._activate_next.append((node, None))
        return self

    def activate_next(self, self_activation, **kwargs):
        for next_task in self_activation.next_tasks:
            next_task.activate(self_activation, self_activation.task.token)


class First(Gateway):
    """
    TODO: Wait for first of outgoing task to be completed and cancells all others
    """
    task_type = 'FIRST_OF'

    def __init__(self):
        super(First, self).__init__()
        self._activate_list = []

    def _outgoing(self):
        for next_node in self._activate_next:
            yield Edge(src=self, dst=next_node, edge_class='next')

    def Of(self, node):
        self._activate_list.append(node)
        return self

    def activate(self, prev_activation):
        pass  # TODO
