try:
    from unittest import mock
except ImportError:
    import mock

from django.test import TestCase

from viewflow import activation, flow, lock
from viewflow.activation import STATUS


class Test(TestCase):
    class ProcessStub(object):
        _default_manager = mock.Mock()

        def __init__(self, flow_class=None):
            self.flow_class = flow_class

        def active_tasks(self):
            return []

        def save(self):
            self.pk = 1
            return

    ProcessStub._default_manager.get.return_value = ProcessStub()

    class TaskStub(object):
        process_id = 1
        status = STATUS.NEW

        def __init__(self, flow_task=None):
            self.flow_task = flow_task
            self.started = None

        @property
        def leading(self):
            from viewflow.models import Task
            return Task.objects.none()

        def save(self):
            self.pk = 1
            return

    class UserStub(object):
        pass

    def init_node(self, node):
        class FlowStub(object):
            process_class = Test.ProcessStub
            lock_impl = staticmethod(lock.no_lock)
            task_class = Test.TaskStub
            instance = None

        node.flow_class = FlowStub()

        return node

    def test_activation_context_scope(self):
        with activation.Context(first_scope='first_scope'):
            with activation.Context(second_scope='second_scope'):
                self.assertEqual(activation.context.first_scope, 'first_scope')
                self.assertEqual(activation.context.second_scope, 'second_scope')

            self.assertEqual(activation.context.first_scope, 'first_scope')
            self.assertTrue(hasattr(activation.context, 'first_scope'))
            self.assertFalse(hasattr(activation.context, 'second_scope'))

        self.assertFalse(hasattr(activation.context, 'first_scope'))
        self.assertFalse(hasattr(activation.context, 'second_scope'))

    def test_startactivation_lifecycle(self):
        flow_task = self.init_node(flow.Start())

        act = activation.StartActivation()
        act.initialize(flow_task, None)

        # execute
        act.prepare()
        act.done()
        self.assertEqual(act.task.status, STATUS.DONE)

        # undo
        act.undo()
        self.assertEqual(act.task.status, STATUS.CANCELED)

    def test_viewactivation_lifecycle(self):
        flow_task = self.init_node(flow.View(lambda _: None))

        act = activation.ViewActivation()
        act.initialize(flow_task, Test.TaskStub())

        # check assign/reassign flow
        act.assign(Test.UserStub())
        self.assertEqual(act.task.status, STATUS.ASSIGNED)
        self.assertIsNotNone(act.task.assigned)

        act.reassign(Test.UserStub())
        self.assertEqual(act.task.status, STATUS.ASSIGNED)
        self.assertIsNotNone(act.task.assigned)

        act.unassign()
        self.assertEqual(act.task.status, STATUS.NEW)
        self.assertIsNone(act.task.assigned)

        # execute
        act.assign(Test.UserStub())
        act.prepare()
        act.done()

        # undo
        act.undo()
        self.assertEqual(act.task.status, STATUS.NEW)
        act.cancel()
        self.assertEqual(act.task.status, STATUS.CANCELED)

    def test_gateactivation_lifecycle(self):
        class GateActivation(activation.AbstractGateActivation):
            def __init__(self, *args, **kwargs):
                self.throw_error = kwargs.pop('throw_error', False)
                super(GateActivation, self).__init__(*args, **kwargs)

            def calculate_next(self):
                if self.throw_error:
                    raise ValueError('Gate Error')

            def activate_next(self):
                pass

        flow_task = self.init_node(flow.Node())

        # construct gate that throws error
        act = GateActivation(throw_error=True)
        act.initialize(flow_task, Test.TaskStub())

        # by default gate exceptions are propogated
        self.assertRaises(ValueError, act.perform)

        # disable gate error propagation
        with activation.Context(propagate_exception=False):
            act.perform()
            self.assertEqual(act.task.status, STATUS.ERROR)

            act.retry()
            self.assertEqual(act.task.status, STATUS.ERROR)

        # fix gate data and retry
        act.throw_error = False
        act.retry()
        self.assertEqual(act.task.status, STATUS.DONE)

        # undo
        act.undo()
        self.assertEqual(act.task.status, STATUS.NEW)
        act.cancel()
        self.assertEqual(act.task.status, STATUS.CANCELED)

    def test_jobactivation_lifecycle(self):
        class JobActivation(activation.AbstractJobActivation):
            def __init__(self, *args, **kwargs):
                self.throw_on_schedule_error = kwargs.pop('throw_on_schedule_error', False)
                super(JobActivation, self).__init__(*args, **kwargs)

            def run_async(self):
                if self.throw_on_schedule_error:
                    raise ValueError('Job scheduler error')

            def activate_next(self):
                pass

        flow_task = self.init_node(flow.Node())

        # construct job that throws error on schedule
        act = JobActivation(throw_on_schedule_error=True)
        act.initialize(flow_task, Test.TaskStub())

        # by default job exceptions are propogated
        act.assign()
        self.assertEqual(act.task.status, STATUS.ASSIGNED)
        self.assertRaises(ValueError, act.schedule)

        # disable error propagation
        with activation.Context(propagate_exception=False):
            act.schedule()
            act.retry()
            self.assertEqual(act.task.status, STATUS.ERROR)

        act.throw_on_schedule_error = False
        act.retry()
        self.assertEqual(act.task.status, STATUS.SCHEDULED)

        # faild job execution
        act.start()
        self.assertEqual(act.task.status, STATUS.STARTED)
        act.error()
        self.assertEqual(act.task.status, STATUS.ERROR)

        # successful job execution
        act.retry()
        self.assertEqual(act.task.status, STATUS.SCHEDULED)
        act.start()
        self.assertEqual(act.task.status, STATUS.STARTED)
        act.done()
        self.assertEqual(act.task.status, STATUS.DONE)

        # undo
        act.undo()
        self.assertEqual(act.task.status, STATUS.ASSIGNED)
        act.cancel()
        self.assertEqual(act.task.status, STATUS.CANCELED)

    def test_endactivation_lifecycle(self):
        flow_task = self.init_node(flow.End())

        # construct job that throws error on schedule
        act = activation.EndActivation()
        act.initialize(flow_task, Test.TaskStub())

        # perform
        act.perform()
        self.assertEqual(act.process.status, STATUS.DONE)
