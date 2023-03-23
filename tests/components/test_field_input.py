from selenium.webdriver.common.by import By
from django import forms
from django.test import override_settings
from django.urls import path
from django.views.generic import FormView
from viewflow.urls import Application, Site

from . import LiveTestCase


@override_settings(ROOT_URLCONF=__name__)
class Test(LiveTestCase):
    def test_field_input(self):
        self.browser.get(f"{self.live_server_url}/application/form/")
        self.assertNoJsErrors()

        input = self.browser.find_element(By.CSS_SELECTOR, "vf-field-input input")
        label = self.browser.find_element(By.CSS_SELECTOR, "vf-field-input label")
        label_classes = label.get_attribute("class").split(" ")
        self.assertNotIn("mdc-text-field--float-above", label_classes)

        input.click()
        label_classes = label.get_attribute("class").split(" ")
        self.assertIn("mdc-text-field--focused", label_classes)
        self.assertIn("mdc-text-field--label-floating", label_classes)
        self.assertNoJsErrors()


class TestForm(forms.Form):
    field = forms.CharField()


urlpatterns = [
    path(
        "",
        Site(
            viewsets=[
                Application(
                    title="Test Application",
                    urlpatterns=[
                        path(
                            "form/",
                            FormView.as_view(
                                form_class=TestForm,
                                template_name="tests/components.html",
                            ),
                        )
                    ],
                ),
            ]
        ).urls,
    )
]
