import uuid
from contextlib import contextmanager
from django.db import transaction
from django.utils import timezone

from ..activation import Activation
from ..base import Node
from ..exceptions import FlowRuntimeError
from ..fields import get_flow_ref, import_flow_by_ref
from ..status import STATUS
from . import mixins


class AbstractJobActivation(mixins.NextNodeActivationMixin, Activation):
    @classmethod
    def create(cls, flow_task, prev_activation, token):
        """Instantiate and persist new flow task."""
        flow_class = flow_task.flow_class
        task = flow_class.task_class(
            process=prev_activation.process,
            flow_task=flow_task,
            token=token,
            external_task_id=str(uuid.uuid4())
        )
        task.save()
        task.previous.add(prev_activation.task)
        return cls(task)

    @Activation.status.transition(source=STATUS.SCHEDULED, target=STATUS.STARTED)
    def start(self):
        self.task.started = timezone.now()
        self.task.save()

    @Activation.status.transition(source=STATUS.STARTED, target=STATUS.DONE)
    def complete(self):
        super().complete.original()

    @Activation.status.transition(source=STATUS.STARTED)
    def execute(self):
        self.complete()
        self.activate_next()

    def ref(self):
        return f'{get_flow_ref(self.flow_class)}/{self.process.pk}/{self.task.pk}'


class AbstractJob(
    mixins.NextNodeMixin,
    Node
):
    task_type = 'JOB'

    shape = {
        'width': 150,
        'height': 100,
        'text-align': 'middle',
        'svg': """
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
        """
    }

    bpmn_element = 'scriptTask'

    @staticmethod
    @contextmanager
    def activate(activation_ref):
        try:
            flow_ref, process_pk_ref, task_pk_ref = activation_ref.rsplit('/', 2)
            process_pk, task_pk = int(process_pk_ref), int(task_pk_ref)
        except ValueError as exc:
            raise FlowRuntimeError(f'Invalid activation reference - "{activation_ref}"') from exc

        flow_class = import_flow_by_ref(flow_ref)

        # start
        with transaction.atomic(), flow_class.lock(process_pk):
            try:
                task = flow_class.task_class.objects.get(pk=task_pk, process_id=process_pk)
                if task.status == STATUS.CANCELED:
                    return
            except flow_class.task_class.DoesNotExist:
                # There was rollback on job task created transaction,
                # we don't need to do the job
                return
            else:
                activation = task.flow_task.activation_class(task)
                activation.start()

        try:
            yield activation  # long-running job without lock
        except Exception as exc:
            # error
            with transaction.atomic(), flow_class.lock(process_pk):
                activation = task.flow_task.activation_class(task)
                activation.error(exc)
            raise exc
        else:
            # success
            with transaction.atomic(), flow_class.lock(process_pk):
                activation = task.flow_task.activation_class(task)
                activation.execute()
