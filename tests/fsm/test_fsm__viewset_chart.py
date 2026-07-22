"""FSM viewset state-chart view tests.

`FlowViewsMixin` had no way for a general (non-admin) user to see the
state machine diagram that `FlowAdminMixin` already renders in the
Django admin. The `chart()` function (DOT output) existed, but no view
or URL exposed it outside admin.
"""

from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase, override_settings
from django.urls import path

from viewflow import fsm
from viewflow.fsm import FlowViewsMixin
from viewflow.urls import ReadonlyModelViewset


class TicketState(models.TextChoices):
    NEW = "NEW", "New"
    DONE = "DONE", "Done"


class ChartTicket(models.Model):
    stage = models.CharField(max_length=20, default=TicketState.NEW)

    class Meta:
        app_label = "tests"


class ChartTicketFlow:
    stage = fsm.State(TicketState, default=TicketState.NEW)

    def __init__(self, ticket):
        self.ticket = ticket

    @stage.setter()
    def _set_stage(self, value):
        self.ticket.stage = value

    @stage.getter()
    def _get_stage(self):
        return self.ticket.stage

    @stage.transition(source=TicketState.NEW, target=TicketState.DONE, permission=None)
    def complete(self):
        pass


class ChartTicketViewset(FlowViewsMixin, ReadonlyModelViewset):
    model = ChartTicket
    flow_state = ChartTicketFlow.stage
    list_ordering_fields = "pk"

    def get_object_flow(self, request, obj):
        return ChartTicketFlow(obj)


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):  # noqa: D101
    def setUp(self):
        self.user = User.objects.create_superuser("admin", "admin@admin.com", "admin")
        self.assertTrue(self.client.login(username="admin", password="admin"))

    def test_chart_view_renders_the_state_diagram(self):
        response = self.client.get("/tickets/chart/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "digraph")
        self.assertContains(response, "NEW")
        self.assertContains(response, "DONE")

    def test_chart_action_listed_on_list_page(self):
        response = self.client.get("/tickets/")

        self.assertContains(response, "/tickets/chart/")

    def test_list_page_shows_flow_diagram_with_export(self):
        response = self.client.get("/tickets/")

        self.assertEqual(response.status_code, 200)
        # The state diagram is embedded next to the object table ...
        self.assertContains(response, "<vf-network")
        self.assertContains(response, "digraph")
        # ... together with a PNG export control.
        self.assertContains(response, "data-vf-network-export")
        self.assertContains(response, "chartticket-flow.png")


urlpatterns = [
    path("tickets/", ChartTicketViewset(app_name="tickets").urls),
]
