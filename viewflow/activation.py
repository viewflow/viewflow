from viewflow.exceptions import FlowRuntimeError


class Activation(object):
    def __init__(self, task):
        self.task = task

    def activate(self):
        self.task.activate()

    def start(self, data):
        self.task.start()

    def done(self):
        self.task.done()


class StartActivation(Activation):
    def __init__(self, flow_task, task_cls, data=None):
        self.data = data
        self.flow_cls = flow_task.flow_cls
        self.process = self.flow_cls.process_cls(flow_cls=self.flow_cls)
        self.task = task_cls(process=self.process, flow_task=flow_task)
        self.form = self.flow_cls.activation_form_cls(data=data, instance=self.task)
        if data:
            if self.form.is_valid():
                raise FlowRuntimeError('Activation metadata is broken {}'.format(self.form.errors))
            else:
                self.task = self.form.save(commit=False)

        super(StartActivation, self).__init__(self.task)

    def activate(self):
        if not self.data:
            self.task.activate()

    def start(self):
        if not self.data:
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
