import traceback

from django.db import transaction
from django.utils.timezone import now


from viewflow import signals
from viewflow.activation import Activation, STATUS, context
from viewflow.flow import base


class ItemsSubprocessActivation(Activation):
    @Activation.status.transition(source=STATUS.NEW, target=STATUS.STARTED)
    def start(self):
        try:
            with transaction.atomic(savepoint=True):
                self.task.started = now()
                self.task.save()

                signals.task_started.send(sender=self.flow_cls, process=self.process, task=self.task)

                for item in self.flow_task.items_source(self.process):
                    self.start_handler(item)

        except Exception as exc:
            if not context.propagate_exception:
                self.task.comments = "{}\n{}".format(exc, traceback.format_exc())
                self.task.finished = now()
                self.set_status(STATUS.ERROR)
                self.task.save()
                signals.task_failed.send(sender=self.flow_cls, process=self.process, task=self.task)
            else:
                raise

    def is_done(self):
        subprocess_cls = self.flow_task.start_handler.process_cls
        subprocesses = subprocess_cls._default_manager.filter(parent_task=self.task).exclude(status=STATUS.DONE).exists()
        return not subprocesses


class ItemsSubprocess(base.NextNodeMixin, base.DetailsViewMixin, base.Gateway):
    task_type = 'SUBPROCESS'
    activation_Cls = ItemsSubprocessActivation

    def __init__(self, start_handler, items_source):
        self.start_handler = start_handler
        self.items_source = items_source

    def on_flow_finished(self, **signal_kwargs):
        process = signal_kwargs['process']

        if process.parent_task:
            activation = self.activation_cls()
            activation.initialize(self, process.parent_task)
            if activation.is_done():
                activation.done()

    def ready(self):
        signals.flow_finished.connect(self.on_flow_finished, sender=self.start_handler.flow_cls)

    @classmethod
    def activate(cls, flow_task, prev_activation, token):
        flow_cls, flow_task = flow_task.flow_cls, flow_task
        process = prev_activation.process

        task = flow_cls.task_cls(
            process=process,
            flow_task=flow_task,
            token=token)

        task.save()
        task.previous.add(prev_activation.task)

        activation = cls()
        activation.initialize(flow_task, task)

        activation.start()

        return activation
