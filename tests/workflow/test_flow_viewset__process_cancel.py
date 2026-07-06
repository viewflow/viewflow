from django.contrib.auth.models import User, Permission
from django.contrib.messages import get_messages
from django.test import TestCase, override_settings
from django.urls import path

from viewflow import this
from viewflow.workflow import Flow, PROCESS, flow
from viewflow.workflow.flow import views
from viewflow.workflow.models import Process


@override_settings(ROOT_URLCONF=__name__)
class TestProcessCancelPermission(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.viewer = User.objects.create_user(username="viewer", password="pwd")
        cls.viewer.user_permissions.add(
            Permission.objects.get(codename="view_testprocesscancelprocess")
        )
        cls.manager = User.objects.create_user(username="manager", password="pwd")
        cls.manager.user_permissions.add(
            Permission.objects.get(codename="view_testprocesscancelprocess"),
            Permission.objects.get(codename="manage_testprocesscancelprocess"),
        )

    def _start_process(self):
        return TestProcessCancelFlow.start.run()

    def test_view_only_user_cant_cancel_process(self):
        process = self._start_process()
        self.assertTrue(self.client.login(username="viewer", password="pwd"))

        response = self.client.post(
            f"/{process.pk}/cancel/", {"_cancel_process": ""}
        )

        self.assertEqual(403, response.status_code)
        process.refresh_from_db()
        self.assertNotEqual(PROCESS.CANCELED, process.status)

    def test_manager_can_cancel_process(self):
        process = self._start_process()
        self.assertTrue(self.client.login(username="manager", password="pwd"))

        response = self.client.post(
            f"/{process.pk}/cancel/", {"_cancel_process": ""}
        )

        self.assertEqual(302, response.status_code)
        process.refresh_from_db()
        self.assertEqual(PROCESS.CANCELED, process.status)


@override_settings(ROOT_URLCONF=__name__)
class TestProcessCancelFlashMessages(TestCase):
    # CancelProcessView.post's flash messages used plain gettext_lazy
    # strings with an f-string-style placeholder ("Process #{self.
    # object.pk} ...") but no f-string prefix and no .format() call --
    # the placeholder was never substituted and rendered literally.
    @classmethod
    def setUpTestData(cls):
        cls.manager = User.objects.create_user(username="manager2", password="pwd")
        cls.manager.user_permissions.add(
            Permission.objects.get(codename="view_testprocesscancelprocess"),
            Permission.objects.get(codename="manage_testprocesscancelprocess"),
        )

    def test_cancel_success_message_substitutes_the_pk(self):
        process = TestProcessCancelFlow.start.run()
        self.assertTrue(self.client.login(username="manager2", password="pwd"))

        response = self.client.post(
            f"/{process.pk}/cancel/", {"_cancel_process": ""}
        )

        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertEqual(
            messages, [f"Process #{process.pk} has been canceled."]
        )

    def test_already_canceled_error_message_substitutes_the_pk(self):
        process = TestProcessCancelFlow.start.run()
        self.assertTrue(self.client.login(username="manager2", password="pwd"))

        self.client.post(f"/{process.pk}/cancel/", {"_cancel_process": ""})
        response = self.client.post(
            f"/{process.pk}/cancel/", {"_cancel_process": ""}
        )

        # The test client's message storage doesn't get drained between
        # requests the way a real response cycle would, so both the
        # earlier success message and this call's error message
        # accumulate -- the error message (this test's concern) is the
        # last one.
        messages = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertEqual(messages[-1], f"Process #{process.pk} can not be canceled.")


@override_settings(ROOT_URLCONF=__name__)
class TestProcessCancelCrossFlowIsolation(TestCase):
    """A manage permission scoped to flow A must not cancel flow B's process.

    CancelProcessView.get_queryset() previously returned the unscoped
    ``process_class._default_manager.all()``, which -- since process_class
    is a proxy model sharing the concrete Process table -- let flow A's URL
    load flow B's process row by pk. has_manage_permission() was then
    evaluated against flow A's model-wide permission, and post() canceled
    the process via its own (flow B) instance, both permission-checking and
    the object bypassed.
    """

    def test_manager_of_flow_a_cannot_cancel_flow_b_process(self):
        process_b = FlowBCancelFlow.start.run()

        attacker = User.objects.create_user(username="attacker", password="pwd")
        attacker.user_permissions.add(
            Permission.objects.get(codename="view_testprocesscancelprocess"),
            Permission.objects.get(codename="manage_testprocesscancelprocess"),
        )
        self.assertTrue(self.client.login(username="attacker", password="pwd"))

        response = self.client.post(
            f"/{process_b.pk}/cancel/", {"_cancel_process": ""}
        )

        process_b.refresh_from_db()
        self.assertNotEqual(PROCESS.CANCELED, process_b.status)
        self.assertIn(response.status_code, (403, 404))


class TestProcessCancelProcess(Process):
    class Meta:
        proxy = True


class TestProcessCancelFlow(Flow):
    process_class = TestProcessCancelProcess

    start = flow.StartHandle().Next(this.task)
    task = flow.View(views.UpdateProcessView.as_view(fields=[])).Next(this.end)
    end = flow.End()


class FlowBCancelProcess(Process):
    class Meta:
        proxy = True


class FlowBCancelFlow(Flow):
    process_class = FlowBCancelProcess

    start = flow.StartHandle().Next(this.task)
    task = flow.View(views.UpdateProcessView.as_view(fields=[])).Next(this.end)
    end = flow.End()


urlpatterns = [
    path("", flow.FlowAppViewset(TestProcessCancelFlow).urls),
    path("flow_b/", flow.FlowAppViewset(FlowBCancelFlow).urls),
]
