from viewflow.flow.base import Event, Edge


class Timer(Event):
    """
    TODO: Timer activated event task
    """
    task_type = 'TIMER'

    def __init__(self, minutes=None, hours=None, days=None):
        super(Timer, self).__init__()
        self._activate_next = []

    def _outgoing(self):
        for next_node in self._activate_next:
            yield Edge(src=self, dst=next_node, edge_class='next')

    def Next(self, node):
        self._activate_next.append(node)
        return self
