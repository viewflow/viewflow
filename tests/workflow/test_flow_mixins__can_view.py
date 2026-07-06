from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import path
from guardian.shortcuts import assign_perm

from viewflow import this
from viewflow.workflow import Flow, flow
from viewflow.workflow.models import Process


def _noop(activation):
    pass


class TestCanViewProcess(Process):
    # A concrete (multi-table-inheritance) subclass, not a proxy model --
    # matching the pattern real flows use (e.g. HelloWorldProcess).
    # guardian.ctypes.get_content_type() always resolves an object's
    # *concrete* model, so a proxy Process here would never match the
    # content type its own auto-created permission was filed under.
    pass


class TestCanViewFlow(Flow):
    process_class = TestCanViewProcess

    start = flow.StartHandle().Next(this.func)
    func = flow.Function(_noop).Next(this.end)
    end = flow.End()


# A standalone FlowViewset mount (no Application/Site wrapper), so the
# only permission gate on the way to can_view is the task-detail view's
# own -- an outer app/site-level check would require a coarser,
# model-wide permission before ever reaching the per-task check this
# test is about.
urlpatterns = [path("", flow.FlowViewset(TestCanViewFlow).urls)]


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):
    def test_object_level_view_permission_on_the_process_grants_task_detail_access(self):
        # NodeDetailMixin.can_view called has_view_permission(user, task),
        # passing a Task as the `obj` for a process_class permission
        # check. Guardian's object-level lookup matches by the object's
        # own content type, so a permission granted on the *process*
        # never matched a check against the *task* -- a user with only
        # object-level (not model-wide) view permission on the process
        # was wrongly denied.
        process = TestCanViewFlow.start.run()
        task = process.task_set.get(flow_task=TestCanViewFlow.func)

        user = User.objects.create_user(username="viewer", password="pwd")
        assign_perm("view_testcanviewprocess", user, process)

        self.assertTrue(self.client.login(username="viewer", password="pwd"))
        response = self.client.get(task.reverse("detail"))

        self.assertEqual(response.status_code, 200)
