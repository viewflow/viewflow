from dash import dcc, html
from dash.dependencies import Input, Output
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import path

from viewflow.contrib.plotly import Dashboard
from viewflow.urls import Site


dashboard = Dashboard(
    app_name="dashboard",
    title="Test dashboard",
    layout=html.Div(
        [
            dcc.Input(id="secret-input", value="hidden"),
            html.Div(id="secret-output"),
        ]
    ),
)


@dashboard.callback(Output("secret-output", "children"), [Input("secret-input", "value")])
def reveal_secret(value):
    return f"secret is {value}"


site = Site(
    title="Test site",
    # No wrapping Application/permission -- the realistic gap: a developer
    # who forgets to wrap a Dashboard in a permission-gated Application.
    viewsets=[dashboard],
)

urlpatterns = [path("", site.urls)]


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):  # noqa: D101
    def test_layout_endpoint_requires_authentication(self):
        response = self.client.get("/dashboard/_dash-layout/")
        self.assertEqual(response.status_code, 403)

    def test_dependencies_endpoint_requires_authentication(self):
        response = self.client.get("/dashboard/_dash-dependencies/")
        self.assertEqual(response.status_code, 403)

    def test_update_component_endpoint_requires_authentication(self):
        response = self.client.post(
            "/dashboard/_dash-update-component",
            data='{"output":"secret-output.children","outputs":{"id":"secret-output","property":"children"},"inputs":[{"id":"secret-input","property":"value","value":"hidden"}]}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_authenticated_user_can_still_use_the_dashboard(self):
        # Regression guard: the fix must not lock out legitimate users.
        user = User.objects.create_user("dashuser", password="pwd")
        self.client.force_login(user)

        self.assertEqual(self.client.get("/dashboard/_dash-layout/").status_code, 200)
        self.assertEqual(
            self.client.get("/dashboard/_dash-dependencies/").status_code, 200
        )
        response = self.client.post(
            "/dashboard/_dash-update-component",
            data='{"output":"secret-output.children","outputs":{"id":"secret-output","property":"children"},"inputs":[{"id":"secret-input","property":"value","value":"hidden"}]}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"secret is hidden", response.content)
