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
            '<div class="vf-form__hiddenfields"><input id="id_promocode" name="promocode"'
            ' label="Promocode" type="hidden"></div>'
            '<div class="vf-form__visiblefields mdc-layout-grid__inner">'
            '<div class="mdc-layout-grid__cell mdc-layout-grid__cell--span-12">'
            '<vf-field-input required="required" id="id_username" name="username" label="Username"'
            ' type="text"></vf-field-input></div></div></div>',
        )

    def test_render_form_field_error(self):
        renderer = FormLayout()
        content = renderer.render(TestForm(data={}))
        self.assertEqual(
            content,
            '<div class="vf-form mdc-layout-grid"><div class="vf-form__errors">'
            '<div class="vf-form__error">Form error</div></div>'
            '<div class="vf-form__hiddenfields"><input id="id_promocode" name="promocode"'
            ' label="Promocode" type="hidden"></div>'
            '<div class="vf-form__visiblefields mdc-layout-grid__inner">'
            '<div class="mdc-layout-grid__cell mdc-layout-grid__cell--span-12">'
            '<vf-field-input required="required" aria-invalid="true" id="id_username" name="username"'
            ' label="Username" error="This field is required." type="text"></vf-field-input></div></div></div>',
        )

    def test_render_form_hidden_field_error(self):
        renderer = FormLayout()
        content = renderer.render(TestForm(data={"promocode": "invalid"}))
        self.assertEqual(
            content,
            '<div class="vf-form mdc-layout-grid"><div class="vf-form__errors">'
            '<div class="vf-form__error">Form error</div>'
            '<div class="vf-form__error">Promocode must be empty</div>'
            "</div>"
            '<div class="vf-form__hiddenfields"><input id="id_promocode" name="promocode"'
            ' value="invalid" label="Promocode" error="Promocode must be empty" type="hidden"></div>'
            '<div class="vf-form__visiblefields mdc-layout-grid__inner">'
            '<div class="mdc-layout-grid__cell mdc-layout-grid__cell--span-12">'
            '<vf-field-input required="required" aria-invalid="true" id="id_username" name="username"'
            ' label="Username" error="This field is required." type="text"></vf-field-input></div></div></div>',
        )


class TestForm(forms.Form):
    username = forms.CharField()
    promocode = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_promocode(self):
        promo = self.cleaned_data.get("promocode", "")
        if promo:
            raise forms.ValidationError("Promocode must be empty")

    def clean(self):
        raise forms.ValidationError("Form error")
