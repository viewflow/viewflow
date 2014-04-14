from viewflow.exceptions import FlowRuntimeError
from viewflow.flow.base import Gateway, Edge


class If(Gateway):
    """
    Activates one of paths based on condition
    """
    task_type = 'IF'

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

    def activate(self, prev_activation):
        activation = self.activation_cls(self)
        activation.activate(prev_activation)

        activation.start()
        cond_result = self._condition(activation)
        activation.done()

        if cond_result:
            self._on_true.activate(activation)
        else:
            self._on_false.activate(activation)

        return activation


class Switch(Gateway):
    """
    Activates first path with matched condition
    """
    task_type = 'SWITCH'

    def __init__(self):
        super(Switch, self).__init__()
        self._activate_next = []

    def _outgoing(self):
        for next_node, cond in self._activate_next:
            edge_class = 'cond_true' if cond else 'default'
            yield Edge(src=self, dst=next_node, edge_class=edge_class)

    def Case(self, node, cond=None):
        self._activate_next.append((node, cond))
        return self

    def Default(self, node):
        self._activate_next.append((node, None))
        return self

    def activate(self, prev_activation):
        activation = self.activation_cls(self)
        activation.activate(prev_activation)

        activation.start()

        next_task = None
        for node, cond in self._activate_next:
            if cond:
                if cond():
                    next_task = node
                    break
            else:
                next_task = node

        activation.done()

        if next_task:
            next_task.activate(activation)
        else:
            raise FlowRuntimeError('Switch have no positive condition')

        return activation


class Join(Gateway):
    """
    Wait for one or all incoming links and activate next path
    """
    task_type = 'JOIN'

    def __init__(self, wait_all=False):
        super(Join, self).__init__()
        self._wait_all = wait_all
        self._activate_next = []

    def _outgoing(self):
        for next_node in self._activate_next:
            yield Edge(src=self, dst=next_node, edge_class='next')

    def Next(self, node):
        self._activate_next.append(node)
        return self

    def activate(self, prev_activation):
        """
        TODO
        # lookup for active join instance
        tasks = Task.objects.filter(
            flow_task=self,
            process=prev_activation.process,
            status=Task.STATUS.STARTED)

        if len(tasks) > 1:
            raise FlowRuntimeError('More than one join instance for process found')

        task = tasks.first()
        if task:
            activation = self.activation_cls(self, task)
            activation.task.previous.add(prev_activation)
            activation.task.save()
        else:
            activation = self.activation_cls(self)
            activation.activate(prev_activation)
            activation.start()

        # check are we done
        all_links = set(x.src for x in self._incoming())
        finished_links = set(task.flow_task for task in activation.task.previous.all())
        if finished_links == all_links:
            activation.done()

            for outgoing in self._outgoing():
                outgoing.dst.activate(activation)

        return activation
        """


class Split(Gateway):
    """
    Activate outgoing path in-parallel depends on per-path condition
    """
    task_type = 'SPLIT'

    def __init__(self):
        super(Split, self).__init__()
        self._activate_next = []

    def _outgoing(self):
        for next_node, cond in self._activate_next:
            edge_class = 'cond_true' if cond else 'default'
            yield Edge(src=self, dst=next_node, edge_class=edge_class)

    def Next(self, node, cond=None):
        self._activate_next.append((node, cond))
        return self

    def Always(self, node):
        self._activate_next.append((node, None))
        return self

    def activate(self, prev_activation):
        activation = self.activation_cls(self)
        activation.activate(prev_activation)

        activation.start()

        next_tasks = []
        for node, cond in self._activate_next:
            if cond:
                if cond(activation):
                    next_tasks.append(node)
            else:
                next_tasks.append(node)

        activation.done()

        if next_tasks:
            for next_task in next_tasks:
                next_task.activate(activation)
        else:
            raise FlowRuntimeError('No active tasks after split')

        return activation


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
