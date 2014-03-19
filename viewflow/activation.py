from viewflow.exceptions import FlowRuntimeError
from viewflow.models import Task


class Activation(object):
    """
    Base class for managing flow task activation state

    By default any state changes saved to db
    """
    def __init__(self, flow_task, task=None):
        self.task = task
        self.process = task.process if task else None
        self.flow_task = flow_task
        self.flow_cls = self.flow_task.flow_cls

    def activate(self, prev_activation):
        self.process = prev_activation.process
        self.task = self.flow_cls.task_cls(process=self.process, flow_task=self.flow_task)
        self.task.save()

        self.task.previous.add(prev_activation.task)
        self.task.activate()
        self.task.save()

    def start(self, data=None):
        self.task.start()
        self.task.save()

    def done(self):
        self.task.done()
        self.task.save()


class StartActivation(Activation):
    """
    Create and start flow process activation
    Track and save activation data from user form

    start() call do not save data and suitable for calling on GET requests
    """
    def __init__(self, flow_task):
        super(StartActivation, self).__init__(flow_task)
        self.form = None

    def activate(self, prev_activation):
        raise NotImplementedError

    def start(self, data=None):
        self.process = self.flow_cls.process_cls(flow_cls=self.flow_cls)
        self.task = self.flow_cls.task_cls(process=self.process, flow_task=self.flow_task)

        if not data:
            self.task.activate()
            self.task.start()

        self.form = self.flow_cls.activation_form_cls(data=data, instance=self.task)

        if data:
            if self.form.is_valid():
                self.task = self.form.save(commit=False)
                self.task.status = Task.STATUS.STARTED
            else:
                raise FlowRuntimeError('Activation metadata is broken {}'.format(self.form.errors))

    def done(self):
        # Create process
        self.process.save()
        self.task.process = self.process

        # Finish activation
        self.task.done()
        self.task.save()

        # Start process
        self.task.process.start()
        self.process.save()


class ViewActivation(Activation):
    """
    Track and save activation data from user form

    start() call do not save data and suitable for calling on GET requests
    """
    def __init__(self, flow_task, task=None):
        super(ViewActivation, self).__init__(flow_task, task=task)
        self.form = None

    def start(self, data=None):
        if not data:
            self.task.start()

        self.form = self.flow_cls.activation_form_cls(data=data, instance=self.task)

        if data:
            if self.form.is_valid():
                self.task = self.form.save(commit=False)
                self.task.status = Task.STATUS.STARTED
            else:
                raise FlowRuntimeError('Activation metadata is broken {}'.format(self.form.errors))


class EndActivation(Activation):
    """
    Finish the flow process
    """
    def done(self):
        super(EndActivation, self).done()
        self.process.finish()
        self.process.save()
