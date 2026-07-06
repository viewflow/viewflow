from selenium.webdriver.common.by import By
from django import forms
from django.test import override_settings
from django.urls import path
from django.views.generic import FormView

from . import LiveTestCase


class TestForm(forms.Form):
    field = forms.TimeField(required=False)


urlpatterns = [
    path(
        "form/",
        FormView.as_view(
            form_class=TestForm,
            template_name="tests/components.html",
        ),
    )
]


@override_settings(ROOT_URLCONF=__name__)
class Test(LiveTestCase):
    def test_no_broken_dialog_trigger_and_typed_value_is_kept(self):
        # The trailing clock icon used trailingIcon (renders a plain,
        # non-interactive <i> with no click handler) instead of
        # trailingButton (renders a <button onClick=...>), so
        # onTrailingButtonClick was never wired -- the time-picker dialog
        # was permanently unreachable. Its inner hour/minute inputs were
        # also completely unwired (no value/onChange), so even reaching
        # it wouldn't have helped. Removed the dead dialog UI; the field
        # is a plain, directly-typeable time input.
        self.browser.get(f"{self.live_server_url}/form/")
        self.assertNoJsErrors()

        dialogs = self.browser.find_elements(By.CSS_SELECTOR, "vf-field-time .mdc-dialog")
        self.assertEqual(dialogs, [])

        text_input = self.browser.find_element(By.CSS_SELECTOR, "vf-field-time input")
        text_input.send_keys("14:30:00")

        self.assertEqual(text_input.get_property("value"), "14:30:00")
        self.assertNoJsErrors()
