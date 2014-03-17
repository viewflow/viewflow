from viewflow.exceptions import FlowRuntimeError


class Activation(object):
    def activate(self, prev_activation):
        raise NotImplementedError

    def start(self, data):
        raise NotImplementedError

    def done(self):
        raise NotImplementedError


class StartActivation(Activation):
    def __init__(self, flow_task, data=None):
        self.data = data
        self.flow_cls = flow_task.flow_cls
        self.process = self.flow_cls.process_cls(flow_cls=self.flow_cls)
        self.task = self.flow_cls.task_cls(process=self.process, flow_task=flow_task)
        self.form = self.flow_cls.activation_form_cls(data=data, instance=self.task)

        if data:
            if self.form.is_valid():
                raise FlowRuntimeError('Activation metadata is broken {}'.format(self.form.errors))
            else:
                self.task = self.form.save(commit=False)

    def start(self):
        if not self.data:
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
    def __init__(self, flow_task, task, data=None):
        self.task = task

    @staticmethod
    def activate(self, flow_task, prev_activation):
        #activation.save()
        #activation.previous.add(prev_activation)
        #return activation
        pass
