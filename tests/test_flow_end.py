from django.test import TestCase

from viewflow import flow
from viewflow.activation import STATUS
from viewflow.base import this, Flow
from viewflow.models import Task


class Test(TestCase):
    def test_process_with_completed_tasks_done(self):
        act = FlowEndTestFlow.start.run()
        task = act.process.get_task(FlowEndTestFlow.task)
        act = task.activate()
        act.prepare()
        act.done()

        act.process.refresh_from_db()
        self.assertEqual(act.process.status, STATUS.DONE)

    def test_process_with_unfinished_tasks_continues(self):
        act = FlowEndTestFlow.start.run()
        end = Task.objects.create(process=act.process, flow_task=FlowEndTestFlow.end)

        act = end.activate()
        act.perform()

        act.task.refresh_from_db()
        act.process.refresh_from_db()
        self.assertEqual(act.task.status, STATUS.DONE)
        self.assertEqual(act.process.status, STATUS.NEW)


class FlowEndTestFlow(Flow):
    start = flow.StartFunction().Next(this.task)
    task = flow.Function(lambda t: None).Next(this.end)
    end = flow.End()
