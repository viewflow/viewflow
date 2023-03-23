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

        wrapper = self.browser.find_element(By.CSS_SELECTOR, ".mdc-checkbox")
        input = self.browser.find_element(By.CSS_SELECTOR, "vf-field-checkbox input")
        wrapper_classes = wrapper.get_attribute("class").split(" ")
        self.assertNotIn("mdc-checkbox--selected", wrapper_classes)

        input.click()
        wrapper_classes = wrapper.get_attribute("class").split(" ")
        self.assertIn("mdc-checkbox--selected", wrapper_classes)
        self.assertNoJsErrors()


class TestForm(forms.Form):
    field = forms.BooleanField()


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
