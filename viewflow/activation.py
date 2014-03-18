from viewflow.exceptions import FlowRuntimeError


class Activation(object):
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

    def done(self):
        self.task.done()
        self.task.save()


class StartActivation(Activation):
    def __init__(self, flow_task):
        super(StartActivation, self).__init__(flow_task)
        self.form = None

    def activate(self, prev_activation):
        raise NotImplementedError

    def start(self, data=None):
        self.process = self.flow_cls.process_cls(flow_cls=self.flow_cls)
        self.task = self.flow_cls.task_cls(process=self.process, flow_task=self.flow_task)
        self.form = self.flow_cls.activation_form_cls(data=data, instance=self.task)

        if data:
            if self.form.is_valid():
                self.task = self.form.save(commit=False)
            else:
                raise FlowRuntimeError('Activation metadata is broken {}'.format(self.form.errors))
        else:
            self.task.activate()
            self.task.start()

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
    def __init__(self, flow_task, task=None):
        super(ViewActivation, self).__init__(flow_task, task=task)
        self.form = None

    def start(self, data=None):
        self.form = self.flow_cls.activation_form_cls(data=data, instance=self.task)

        if data:
            if self.form.is_valid():
                self.task = self.form.save(commit=False)
            else:
                raise FlowRuntimeError('Activation metadata is broken {}'.format(self.form.errors))
        else:
            self.task.start()
