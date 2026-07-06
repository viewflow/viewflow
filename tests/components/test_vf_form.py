import time

from selenium.webdriver.common.by import By
from django.test import override_settings
from django.urls import path
from django.views.generic import TemplateView

from . import LiveTestCase


class TestPageView(TemplateView):
    template_name = "tests/vf_form.html"


urlpatterns = [path("page/", TestPageView.as_view())]


@override_settings(ROOT_URLCONF=__name__)
class Test(LiveTestCase):
    def _load_page_and_disable_buttons(self):
        page_url = f"{self.live_server_url}/page/"
        self.browser.get(page_url)
        time.sleep(0.2)  # let connectedCallback's setTimeout register listeners

        # Trigger the same disabling onSubmit() already does on a real
        # submit, without depending on a real network round-trip (which
        # would replace the DOM and mask the bug under test here).
        self.browser.execute_script("document.querySelector('vf-form').onSubmit()")
        buttons = self.browser.find_elements(By.CSS_SELECTOR, "vf-form button")
        for button in buttons:
            self.assertTrue(button.get_property("disabled"))
        return buttons

    def test_fetch_request_error_re_enables_buttons(self):
        # DATA-LOSS/STRANDED-FORM: onSubmit disabled every button and
        # nothing ever re-enabled them. A failed fetch (e.g. offline) never
        # produces a response for Turbo to replace the DOM with, so the
        # form was permanently stuck with disabled buttons -- the user
        # can't even retry.
        buttons = self._load_page_and_disable_buttons()

        self.browser.execute_script(
            "document.dispatchEvent(new CustomEvent("
            "'turbo:fetch-request-error', {bubbles: true}))"
        )

        for button in buttons:
            self.assertFalse(button.get_property("disabled"))

    def test_before_cache_re_enables_buttons(self):
        # DATA-LOSS/STRANDED-FORM: Turbo snapshots the DOM on
        # turbo:before-cache before navigating away, for instant
        # back/forward restores. If that snapshot was taken while the
        # buttons were mid-submit-disabled, navigating Back restored a
        # frozen form the user could never interact with again.
        buttons = self._load_page_and_disable_buttons()

        self.browser.execute_script(
            "document.dispatchEvent(new CustomEvent("
            "'turbo:before-cache', {bubbles: true}))"
        )

        for button in buttons:
            self.assertFalse(button.get_property("disabled"))

    def test_submit_end_re_enables_buttons(self):
        buttons = self._load_page_and_disable_buttons()

        self.browser.execute_script(
            "document.dispatchEvent(new CustomEvent("
            "'turbo:submit-end', {bubbles: true}))"
        )

        for button in buttons:
            self.assertFalse(button.get_property("disabled"))
