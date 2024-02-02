from django import forms
from django.test import TestCase
from viewflow.forms.renderers import FormLayout


class Test(TestCase):
    maxDiff = None

    def test_empty_form_render(self):
        renderer = FormLayout()
        content = renderer.render(TestForm())
        self.assertEqual(
            content,
            '<div class="vf-form mdc-layout-grid">'
            '<div class="vf-form__visiblefields mdc-layout-grid__inner">'
            '<div class="mdc-layout-grid__cell mdc-layout-grid__cell--span-12">'
            '<vf-field-input required="required" id="id_username" name="username" label="Username"'
            ' type="text"></vf-field-input></div></div></div>',
        )

    def _test_render_form_error(self):
        renderer = FormLayout()
        content = renderer.render(TestForm(data={}))
        self.assertEqual(
            content,
            '<div class="vf-form mdc-layout-grid"><div class="vf-form__errors">'
            '<div class="vf-form__error">Form error</div></div>'
            '<div class="vf-form__visiblefields mdc-layout-grid__inner">'
            '<div class="mdc-layout-grid__cell mdc-layout-grid__cell--span-12">'
            '<vf-field-input required="required" id="id_username" name="username" label="Username"'
            ' error="This field is required." type="text"></vf-field-input></div></div></div>',
        )


class TestForm(forms.Form):
    username = forms.CharField()

    def clean(self):
        raise forms.ValidationError("Form error")
