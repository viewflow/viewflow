import time

from selenium.webdriver.common.by import By
from django.test import override_settings
from django.urls import path
from django.views.generic import TemplateView

from . import LiveTestCase


class TestPageView(TemplateView):
    template_name = "tests/vf_page_profile_avatar.html"


urlpatterns = [path("page/", TestPageView.as_view())]


@override_settings(ROOT_URLCONF=__name__)
class Test(LiveTestCase):
    def test_no_file_selected_shows_error_instead_of_throwing(self):
        # onChangeAvatarClick called this.showError(...), but the class
        # only defines _showError(...) -- calling a nonexistent method
        # threw a TypeError. Since the handler is an async arrow
        # function, the throw surfaced as an unhandled promise
        # rejection rather than a synchronous window.onerror, and no
        # error message was ever shown to the user.
        page_url = f"{self.live_server_url}/page/"
        self.browser.get(page_url)
        time.sleep(0.2)  # let connectedCallback's setTimeout wire up listeners
        self.browser.execute_script(
            "window.__rejections = [];"
            "window.addEventListener('unhandledrejection',"
            " (e) => window.__rejections.push(String(e.reason)));"
            "window.__snackbarMessages = [];"
            "window.addEventListener('vf-snackbar:show',"
            " (e) => window.__snackbarMessages.push(e.detail.message));"
        )

        file_input = self.browser.find_element(
            By.CSS_SELECTOR, "vf-page-profile-avatar .vf-page-profile__avatar-change input[type=file]"
        )
        self.browser.execute_script(
            "arguments[0].dispatchEvent(new Event('change', {bubbles: true}))",
            file_input,
        )
        time.sleep(0.2)

        rejections = self.browser.execute_script("return window.__rejections")
        self.assertEqual(rejections, [])

        messages = self.browser.execute_script("return window.__snackbarMessages")
        self.assertEqual(messages, ["No images selected"])
        self.assertNoJsErrors()
