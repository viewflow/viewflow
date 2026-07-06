from django.urls import path, reverse
from django.test import TestCase, override_settings

from viewflow import this
from viewflow.workflow import flow, PROCESS, STATUS
from viewflow.workflow.flow import views
from viewflow.workflow.models import Process


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):  # noqa: D101
    def test_default_start_handle(self):
        process = TestWorkflow.default_start.run()

        self.assertIsNotNone(process.pk)
        self.assertEqual(process.flow_class, TestWorkflow)
        self.assertIsNotNone(process.created)

    def test_custom_start_handle(self):
        result = TestWorkflow.custom_start.run(param1='param1', param2='param2')

        process, task, *params = result

        self.assertIsNotNone(process.pk)
        self.assertEqual(process.flow_class, TestWorkflow)
        self.assertIsNotNone(process.created)

        self.assertIsNotNone(task.pk)
        self.assertEqual(task.flow_task, TestWorkflow.custom_start)
        self.assertIsNotNone(task.started)
        self.assertIsNotNone(task.finished)
        self.assertEqual(task.status, STATUS.DONE)
        self.assertFalse(task.previous.all())
        self.assertTrue(task.leading.all())

        self.assertEqual(params, ['param1', 'param2'])

    def test_start_view(self):
        start_url = reverse('testworkflow:view_start:execute')
        self.assertEqual(start_url, '/view_start/')
        """
        # TODO GET
        # POST
        # check process
        """


class TestWorkflow(flow.Flow):  # noqa: D101
    default_start = (
        flow.StartHandle()
        .Next(this.end)
    )

    custom_start = (
        flow.StartHandle(this.start_flow)
        .Next(this.end)
    )

    view_start = (
        flow.Start(views.CreateProcessView.as_view())
        .Next(this.end)
    )

    end = flow.End()

    def start_flow(self, activation, *, param1=None, param2=None):
        return (activation.process, activation.task, param1, param2)


urlpatterns = [
    path('', TestWorkflow.instance.urls)
]


def _boom(activation):
    raise ValueError("boom")


class TestOrphanProcessFlow(flow.Flow):
    start = flow.StartHandle().Next(this.fail_func)
    fail_func = flow.Function(_boom).Next(this.end)
    end = flow.End()


class TestStartOrphanProcessOnFailure(TestCase):
    def test_synchronously_failing_first_node_does_not_orphan_the_process(self):
        # process.save() in StartActivation.execute() ran before the
        # lock/atomic block, committing in autocommit while task creation
        # (complete() + activate_next(), inside the lock's transaction)
        # wasn't. start.run() is called with no enclosing transaction, so
        # a synchronously-failing first node left the process row behind
        # as PROCESS.NEW with zero tasks.
        with self.assertRaises(ValueError):
            TestOrphanProcessFlow.start.run()

        self.assertEqual(
            Process.objects.filter(flow_class=TestOrphanProcessFlow).count(),
            0,
            "the process row must not survive a rolled-back start",
        )
