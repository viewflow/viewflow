import json
import traceback
import uuid

from django.utils import timezone

from ..activation import Activation
from ..base import Node
from ..context import Context
from ..fields import get_flow_ref
from ..signals import task_failed
from ..status import STATUS
from . import mixins


class AbstractJobActivation(mixins.NextNodeActivationMixin, Activation):
    @classmethod
    def create(cls, flow_task, prev_activation, token, data=None, seed=None):
        """Instantiate and persist new flow task."""
        flow_class = flow_task.flow_class
        task = flow_class.task_class(
            process=prev_activation.process,
            flow_task=flow_task,
            token=token,
            external_task_id=str(uuid.uuid4()),
        )
        task.data = data if data is not None else {}
        task.seed = seed
        task.save()
        task.previous.add(prev_activation.task)
        return cls(task)

    @Activation.status.transition(source=STATUS.SCHEDULED, target=STATUS.STARTED)
    def start(self):
        self.task.started = timezone.now()
        self.task.save()

    @Activation.status.transition(source=STATUS.STARTED)
    def resume(self):
        pass

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.DONE)
    def complete(self):
        super().complete.original()

    @Activation.status.transition(source=STATUS.STARTED)
    def execute(self):
        self.complete()
        with Context(propagate_exception=False):
            self.activate_next()

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.ERROR)
    def error(self, exception):
        if not self.task.data:
            self.task.data = {}

        tb = exception.__traceback__
        while tb.tb_next:
            tb = tb.tb_next

        try:
            serialized_locals = json.dumps(
                tb.tb_frame.f_locals, default=lambda obj: str(obj)
            )
        except Exception as ex:
            serialized_locals = json.dumps({"_serialization_exception": str(ex)})

        self.task.data["_exception"] = {
            "title": str(exception),
            "traceback": traceback.format_exc(),
            "locals": json.loads(serialized_locals),
        }
        self.task.finished = timezone.now()
        self.task.save()
        task_failed.send(sender=self.flow_class, process=self.process, task=self.task)

    def ref(self):
        return f"{get_flow_ref(self.flow_class)}/{self.process.pk}/{self.task.pk}"


class AbstractJob(mixins.NextNodeMixin, Node):
    task_type = "JOB"

    shape = {
        "width": 150,
        "height": 100,
        "text-align": "middle",
        "svg": """
            <rect class="task" width="150" height="100" rx="5" ry="5"/>
            <path class="task-label"
                  d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65
                     c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1
                     c-.52-.4-1.08-.73-1.69-.98l-.38-2.65 C14.46 2.18 14.25 2 14 2
                     h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1
                     c-.23-.09-.49 0-.61.22 l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65
                     c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64
                     l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65
                     c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65
                     c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.09.49 0 .61-.22l2-3.46
                     c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5
                     s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"/>
        """,
    }

    bpmn_element = "scriptTask"
