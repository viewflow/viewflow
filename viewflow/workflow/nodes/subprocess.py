from ..base import Node
from .start import StartActivation
from . import mixins


# TODO StartSubprocessActivation
# TODO SubprocessActivation
# TODO NSubprocessActivation

class StartSubprocess(
    mixins.NextNodeMixin,
    Node
):
    """Start subprocess handle"""
    task_type = 'START'

    shape = {
        'width': 50,
        'height': 50,
        'svg': """
            <circle class="event" cx="25" cy="25" r="25"/>
        """
    }

    bpmn_element = 'startEvent'

    activation_class = StartActivation


class Subprocess(
    mixins.NextNodeMixin,
    Node
):
    task_type = 'SUBPROCESS'

    shape = {
        'width': 150,
        'height': 100,
        'text-align': 'middle',
        'svg': """
            <rect class="task" width="150" height="100" rx="5" ry="5" style="stroke-width:5"/>
        """
    }

    def __init__(self, subflow_task, **kwargs):
        self.subflow_task = subflow_task
        super(Subprocess, self).__init__(**kwargs)


class NSubprocess(Subprocess):
    task_type = 'SUBPROCESS'

    shape = {
        'width': 150,
        'height': 100,
        'text-align': 'middle',
        'svg': """
            <rect class="task" width="150" height="100" rx="5" ry="5" style="stroke-width:5"/>
        """
    }

    def __init__(self, subflow_task, subitem_source, **kwargs):
        self.subflow_task = subflow_task
        self.subitem_source = subitem_source
        super(NSubprocess, self).__init__(subflow_task, **kwargs)
