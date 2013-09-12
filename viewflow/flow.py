"""
Ubiquitos language for flow construction
"""
class FlowMeta(object):
    """
    Flow options
    """
    def __init__(self, meta):
        pass


class FlowMetaClass(type):
    def __new__(cls, name, bases, attrs):
        new_class = super(FlowMetaClass, cls).__new__(cls, name, bases, attrs)

        # set up workflow meta
        meta = getattr(new_class, 'Meta', None)
        new_class._meta = FlowMeta(meta)

        return new_class


class Flow(object, metaclass = FlowMetaClass):
    """
    Base class for flow definition
    """


class _Node(object):
    """
    Base class for flow objects
    """
    def __init__(self):
        self.__role = None

    def Role(self, role):
        self.__role = role
        return self



class _Event(_Node):
    """
    Base class for event-based tasks
    """


class Start(_Node):
    """
    Start process event
    """
    def __init__(self):
        super(Start, self).__init__()
        self.__activate_next = []

    def Activate(self, node):
        self.__activate_next.append(node)
        return self


class End(_Event):
    """
    End process event
    """


class Timer(_Event):
    """
    Timer activated event task
    """
    def __init__(self, minutes=None, hours=None, days=None):
        super(Timer, self).__init__()
        self.__activate_next = []

    def Next(self, node):
        self.__activate_next.append(node)
        return self



class Mailbox(_Event):
    """
    Message activated task
    """
    def __init__(self, on_receive):
        super(Mailbox, self).__init__()
        self.__activate_next = []
        self.__on_receive = on_receive

    def Next(self, node):
        self.__activate_next.append(node)
        return self


class _Task(_Node):
    """
    Base class for algoritmically performed tasks
    """


class View(_Task):
    """
    Human performed task
    """
    def __init__(self, view):
        super(View, self).__init__()
        self.__activate_next = []
        self.__view = view

    def Next(self, node):
        self.__activate_next.append(node)
        return self


class Job(_Task):
    """
    Automatically running task
    """
    def __init__(self, job):
        super(Job, self).__init__()
        self.__activate_next = []
        self.__job = job

    def Next(self, node):
        self.__activate_next.append(node)
        return self


class _Gate(_Node):
    """
    Base class for flow control gates
    """


class If(_Gate):
    """
    Activates one of paths based on condition
    """
    def __init__(self, cond):
        super(If, self).__init__()
        self.__condition = cond
        self.__on_true = None
        self.__on_false = None

    def OnTrue(self, node):
        self.__on_true = node
        return self

    def OnFalse(self, node):
        self.__on_false = node
        return self


class Switch(_Gate):
    """
    Activates first path with matched condition
    """
    def __init__(self):
        super(Split, self).__init__()
        self.__activate_next = []

    def Case(self, node, cond=None):
        self.__activate_next.append((node, cond))
        return self

    def Default(self, node):
        self.__activate_next.append((node, None))
        return self


class Join(_Gate):
    """
    Wait for all incoming links and activates on complete
    """
    def __init__(self):
        super(Join, self).__init__()
        self.__activate_next = []

    def Next(self, node):
        self.__activate_next.append(node)
        return self


class Split(_Gate):
    """
    Activate outgoing path in-parallel depends on per-path condition
    """
    def __init__(self):
        super(Split, self).__init__()
        self.__activate_next = []

    def Next(self, node, cond=None):
        self.__activate_next.append((node, cond))
        return self

    def Always(self, node):
        self.__activate_next.append((node, None))
        return self


class First(_Gate):
    """
    Wait for first of outgoing task to be completed and cancells all others
    """
    def __init__(self):
        super(First, self).__init__()
        self.__activate_list = []

    def Of(self, node):
        self.__activate_list.append(node)
        return self
