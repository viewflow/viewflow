import time

from selenium.webdriver.common.by import By
from django import forms
from django.test import override_settings
from django.urls import path
from django.views.generic import FormView

from . import LiveTestCase


class TestForm(forms.Form):
    field = forms.DateField(required=False)


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
    def test_reopening_the_dialog_does_not_stack_close_listeners(self):
        # onBtnClick registered a new MDCDialog:closing listener on
        # every trailing-button click instead of once next to
        # `new MDCDialog(...)` -- unbounded growth. After N open/close
        # cycles, closing the dialog fired the state-update side effect
        # (textfield.layout()) N times instead of once, since every
        # accumulated listener from prior opens fired too.
        self.browser.get(f"{self.live_server_url}/form/")
        self.assertNoJsErrors()

        self.browser.execute_script(
            """
            window.__layoutCalls = 0;
            const field = document.querySelector('vf-field-date');
            const textfield = field.querySelector('.mdc-text-field').textfield;
            const original = textfield.layout.bind(textfield);
            textfield.layout = (...args) => {
                window.__layoutCalls += 1;
                return original(...args);
            };
            """
        )

        trailing_button = self.browser.find_element(
            By.CSS_SELECTOR, "vf-field-date .vf-text-field__button"
        )

        # A single MDC close can itself fire MDCDialog:closing more than
        # once (its own internal animation-related event bookkeeping),
        # so this doesn't assert an exact per-close count -- it asserts
        # the count *stays flat* across repeated open/close cycles
        # rather than growing, since a growing per-cycle count is what
        # a stacked listener produces (cycle N re-fires N accumulated
        # listeners) while a flat one is what a single, correctly
        # registered-once listener produces.
        per_cycle_counts = []
        for _ in range(3):
            trailing_button.click()
            time.sleep(0.3)
            close_button = self.browser.find_element(
                By.CSS_SELECTOR, "vf-field-date [data-mdc-dialog-action=close]"
            )
            close_button.click()
            time.sleep(0.3)
            per_cycle_counts.append(
                self.browser.execute_script("return window.__layoutCalls")
            )

        deltas = [
            per_cycle_counts[i] - per_cycle_counts[i - 1]
            for i in range(1, len(per_cycle_counts))
        ]
        self.assertEqual(
            deltas,
            [per_cycle_counts[0]] * len(deltas),
            f"per-cycle layout() calls grew instead of staying flat: {per_cycle_counts}",
        )
        self.assertNoJsErrors()
