from django.test import TestCase

from viewflow import activation, flow
from viewflow.compat import mock
from viewflow.models import Task


class ProcessStub(object):
    _default_manager = mock.Mock()

    def __init__(self, *args, **kwargs):
        pass

    def save(self):
        pass


class TaskStub(object):
    process_id = 1
    status = activation.STATUS.NEW
    token = 'start'

    def __init__(self, *args, **kwargs):
        pass

    @property
    def leading(self):
        return Task.objects.none()

    def save(self):
        pass


class UserStub(object):
    pass


class NextTaskStub(object):
    def activate(self, prev_activation, token):
        pass


class FlowStub(object):
    process_cls = ProcessStub
    task_cls = TaskStub
    instance = None


class TestGateAcitation(activation.AbstractGateActivation):
    def __init__(self, *args, **kwargs):
        self.throw_error = kwargs.pop('throw_error', False)
        super(TestGateAcitation, self).__init__(*args, **kwargs)

    def calculate_next(self):
        if self.throw_error:
            raise ValueError('Gate Error')

    @activation.Activation.status.super()
    def activate_next(self):
        pass


class TestJobAcitation(activation.AbstractJobActivation):
    def __init__(self, *args, **kwargs):
        self.throw_on_schedule_error = kwargs.pop('throw_on_schedule_error', False)
        super(TestJobAcitation, self).__init__(*args, **kwargs)

    def async(self):
        if self.throw_on_schedule_error:
            raise ValueError('Job scheduler error')

    @activation.Activation.status.super()
    def activate_next(self):
        pass


class TestActivations(TestCase):
    def init(self, flow_task):
        if hasattr(flow_task, 'Next'):
            flow_task.Next(NextTaskStub())
        flow_task.flow_cls = FlowStub
        return flow_task

    def test_startactivation_lifecycle(self):
        flow_task = self.init(flow.Start())

        act = activation.StartActivation()
        act.initialize(flow_task, None)

        act.prepare()
        act.done()
        act.undo()

    def test_startviewactivation_lifecycle(self):
        act = activation.StartViewActivation()
        act.initialize(self.init(flow.Start()), None)

        act.prepare()
        act.done()
        act.undo()

    def test_viewactivation_lifecycle(self):
        flow_task = self.init(flow.View(lambda _: None))

        act = activation.ViewActivation()
        act.initialize(flow_task, TaskStub())

        # assign
        act.assign(UserStub())
        act.reassign(UserStub())
        act.unassign()
        act.assign(UserStub())

        act.prepare()
        act.done()
        act.undo()
        act.cancel()

    def test_gateactivation_lifecycle(self):
        flow_task = self.init(flow.Node())

        act = TestGateAcitation(throw_error=True)
        act.initialize(flow_task, TaskStub())

        self.assertRaises(ValueError, act.perform)

        with activation.Context(propagate_exception=False):
            act.perform()
            act.retry()

            act.throw_error = False
            act.retry()
            act.undo()
            act.cancel()

    def test_jobactivation_lifecycle(self):
        flow_task = self.init(flow.Node())

        act = TestJobAcitation(throw_on_schedule_error=True)
        act.initialize(flow_task, TaskStub())

        act.assign()
        self.assertRaises(ValueError, act.schedule)

        with activation.Context(propagate_exception=False):
            act.schedule()
            act.retry()
            act.throw_on_schedule_error = False
            act.retry()

            act.start()
            act.error()

            act.retry()
            act.start()
            act.done()
            act.undo()
            act.cancel()
