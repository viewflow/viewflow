import json
import re

from django import forms
from django.test import TestCase
from viewflow.forms.renderers import FormLayout, WidgetRenderer


class Test(TestCase):
    maxDiff = None

    def test_get_renderer_cache_does_not_leak_per_instance(self):
        # WidgetRenderer.get_renderer was @lru_cache(maxsize=None) keyed on
        # the widget *instance*. Django deep-copies widgets per form, so
        # every render created a fresh, never-evicted cache key -- pinning
        # every rendered widget/field/form from GC forever, with zero cache
        # hits.
        WidgetRenderer._get_renderer_for_class.cache_clear()

        class F(forms.Form):
            name = forms.CharField()

        for _ in range(5):
            FormLayout().render(F())

        info = WidgetRenderer._get_renderer_for_class.cache_info()
        self.assertGreater(info.hits, 0)
        self.assertLessEqual(info.currsize, 1)

    def test_grouped_select_choices_are_not_dropped(self):
        # Django's optgroups() yields (group_name, [option-dicts], index);
        # the renderer used to keep only options[0], silently dropping the
        # rest of each optgroup.
        class GroupedChoiceForm(forms.Form):
            fruit = forms.ChoiceField(
                choices=[
                    ("Fruits", [("a", "Apple"), ("b", "Banana")]),
                    ("c", "Cherry"),
                ]
            )

        html = FormLayout().render(GroupedChoiceForm())

        match = re.search(r'optgroups="([^"]*)"', html)
        self.assertIsNotNone(match)
        optgroups = json.loads(match.group(1).replace("&quot;", '"'))
        labels = [entry["options"]["label"] for entry in optgroups]

        self.assertEqual(labels, ["Apple", "Banana", "Cherry"])

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
            '<vf-field-input required="required" aria-invalid="true" aria-describedby="id_username_error" id="id_username" name="username"'
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
            '<vf-field-input required="required" aria-invalid="true" aria-describedby="id_username_error" id="id_username" name="username"'
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
