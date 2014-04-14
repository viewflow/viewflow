from viewflow.flow.base import Event, Edge


class Mailbox(Event):
    """
    TODO: Message activated task
    """
    task_type = 'MAILBOX'

    def __init__(self, on_receive):
        super(Mailbox, self).__init__()
        self._activate_next = []
        self._on_receive = on_receive

    def _outgoing(self):
        for next_node in self._activate_next:
            yield Edge(src=self, dst=next_node, edge_class='next')

    def Next(self, node):
        self._activate_next.append(node)
        return self
