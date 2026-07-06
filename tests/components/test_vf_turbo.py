from django.test import override_settings
from django.urls import path
from django.views.generic import TemplateView

from . import LiveTestCase


class TestPageView(TemplateView):
    template_name = "tests/components.html"


urlpatterns = [path("page/", TestPageView.as_view())]


def _dispatch_before_fetch_response(browser, status):
    browser.execute_script(
        """
        const event = new CustomEvent('turbo:before-fetch-response', {
            detail: {fetchResponse: {response: {status: arguments[0]}}},
        });
        document.dispatchEvent(event);
        """,
        status,
    )


@override_settings(ROOT_URLCONF=__name__)
class Test(LiveTestCase):
    def test_422_does_not_disable_turbo_drive(self):
        # disableTurboOnError fired on any status > 400, but
        # HotwireTurboMiddleware rewrites every re-rendered POST (a form
        # validation error, not an actual error) to 422 -- so the first
        # validation error on any form permanently disabled Turbo drive
        # for the rest of the session.
        page_url = f"{self.live_server_url}/page/"
        self.browser.get(page_url)

        self.assertTrue(self.browser.execute_script("return Turbo.session.drive"))

        _dispatch_before_fetch_response(self.browser, 422)

        self.assertTrue(self.browser.execute_script("return Turbo.session.drive"))

    def test_genuine_server_error_still_disables_turbo_drive(self):
        # Regression guard: a real error status must still disable drive.
        page_url = f"{self.live_server_url}/page/"
        self.browser.get(page_url)

        _dispatch_before_fetch_response(self.browser, 500)

        self.assertFalse(self.browser.execute_script("return Turbo.session.drive"))

    def test_error_does_not_overwrite_existing_onpopstate_handler(self):
        # window.onpopstate = ... overwrote any existing handler (rather
        # than adding a listener via addEventListener), silently
        # dropping other popstate subscribers on the page. Checked
        # without actually firing a popstate event, since the error
        # handler's own effect is to reload the page.
        page_url = f"{self.live_server_url}/page/"
        self.browser.get(page_url)

        self.browser.execute_script(
            "window.onpopstate = function __originalHandler() {};"
        )

        _dispatch_before_fetch_response(self.browser, 500)

        handler_name = self.browser.execute_script(
            "return window.onpopstate ? window.onpopstate.name : null"
        )
        self.assertEqual(handler_name, "__originalHandler")
