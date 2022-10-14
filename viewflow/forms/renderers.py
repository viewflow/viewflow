# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

import json
import re
from copy import copy
from typing import List, Type, Union
from functools import lru_cache
from xml.etree import ElementTree

from django import forms
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_str
from typing import Optional

from django.utils.formats import get_format
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from viewflow.utils import MARKER


AUTO = MARKER("AUTO")


class WidgetRenderer(object):
    tag = "vf-field-input"

    def __init__(
        self,
        root: ElementTree.Element,
        bound_field: forms.BoundField,
        layout_node: Optional["LayoutNode"] = None,
    ):
        self.root = root
        self.bound_field = bound_field
        self.layout_node = layout_node

    def format_value(self, value):
        if isinstance(value, (tuple, list)):
            return ",".join(f"{item}" for item in value)
        return f"{value}"

    def create_root(self, context):
        attrs = {
            key: str(value) if value is not True else key
            for key, value in context["widget"]["attrs"].items()
            if value is not False
        }
        attrs["name"] = context["widget"]["name"]
        value = context["widget"]["value"]
        if value is not None:
            attrs["value"] = self.format_value(value)
        if self.bound_field.label:
            attrs["label"] = self.bound_field.label
        if self.bound_field.errors:
            attrs["error"] = self.bound_field.errors[0]
        if self.bound_field.help_text:
            attrs["help-text"] = self.bound_field.help_text
        return ElementTree.SubElement(self.root, self.tag, **attrs)

    def render(self, template_name, context, request=None):
        return self.create_root(context)

    @staticmethod
    @lru_cache(maxsize=None)
    def get_renderer(widget: forms.Widget) -> "Type[WidgetRenderer]":
        from viewflow.conf import settings

        for widget_class in type(widget).mro()[:-2]:
            try:
                return settings.WIDGET_RENDERERS[widget_class]
            except KeyError:
                continue

        return InputRenderer


class CheckboxRenderer(WidgetRenderer):
    tag = "vf-field-checkbox"


class InputRenderer(WidgetRenderer):
    def create_root(self, context):
        root = super().create_root(context)
        root.attrib["type"] = context["widget"]["type"]
        return root


class FileInputRenderer(InputRenderer):
    tag = "vf-field-file"


class HiddenInputRenderer(WidgetRenderer):
    tag = "input"

    def create_root(self, context):
        root = super().create_root(context)
        root.attrib["type"] = "hidden"
        return root


class MultipleHiddenInputRenderer(WidgetRenderer):
    tag = "input"

    def create_root(self, context):
        parent = self.root
        self.root = ElementTree.SubElement(self.root, "div")

        for subwidget in context["widget"]["subwidgets"]:
            child = super().create_root({"widget": subwidget})
            child.attrib["type"] = "hidden"

        root, self.root = self.root, parent
        return root


class PasswordInputRenderer(InputRenderer):
    tag = "vf-field-password"


class TextareaRenderer(WidgetRenderer):
    tag = "vf-field-textarea"


class TrixEditorRenderer(TextareaRenderer):
    tag = "vf-field-editor"


class InlineCalendarRenderer(InputRenderer):
    tag = "vf-field-inline-calendar"

    def find_target_date_format(self, proposed_formats):
        if not proposed_formats:
            formats = get_format("DATE_INPUT_FORMATS")
        else:
            formats = proposed_formats

        supported_formats = [  # input mask friendly formats
            r"%Y-%m-%d",
            r"%m-%d-%Y",
            r"%Y-%d-%m",
            r"%d-%m-%Y",
        ]
        for date_format in formats:
            lookup = date_format.replace(".", "-").replace("/", "-")
            if lookup in supported_formats:
                separator = date_format[2]
                return lookup.replace("-", separator)

        raise ValueError(
            "Widget should accept one of input-mask friendly date input format."
        )

    def create_root(self, context):
        root = super().create_root(context)

        widget_format = self.bound_field.field.widget.format
        root.attrib["format"] = self.find_target_date_format(
            [widget_format] if widget_format else self.bound_field.field.input_formats
        )
        return root


class DateInputRenderer(InlineCalendarRenderer):
    tag = "vf-field-date"

    def date_format_placeholder(self, date_format):
        i18n = {
            r"%Y": _("YYYY"),
            r"%m": _("MM"),
            r"%d": _("DD"),
        }
        split_format = re.split(r"([.\-/])", date_format)
        items = [i18n.get(item, item) for item in split_format]
        return format_lazy("{}" * len(items), *items)

    def create_root(self, context):
        root = super().create_root(context)
        root.attrib["placeholder"] = self.date_format_placeholder(root.attrib["format"])
        return root


class DateTimeInputRenderer(InlineCalendarRenderer):
    tag = "vf-field-date"

    def find_target_date_format(self, proposed_formats):
        if not proposed_formats:
            formats = get_format("DATE_INPUT_FORMATS")
        else:
            formats = proposed_formats

        supported_formats = [  # input mask friendly formats
            r"%Y-%m-%d %H:%M",
            r"%m-%d-%Y %H:%M",
            r"%Y-%d-%m %H:%M",
            r"%d-%m-%Y %H:%M",
            r"%Y-%m-%d %H:%M:%S",
            r"%m-%d-%Y %H:%M:%S",
            r"%Y-%d-%m %H:%M:%S",
            r"%d-%m-%Y %H:%M:%S",
            r"%b-%d-%Y %I:%M %p",
        ]
        for date_format in formats:
            lookup = date_format.replace(".", "-").replace("/", "-")
            if lookup in supported_formats:
                separator = date_format[2]
                return lookup.replace("-", separator)

        raise ValueError(
            "Widget should accept one of input-mask friendly date input format."
        )

    def date_format_placeholder(self, date_format):
        i18n = {
            r"%Y": _("YYYY"),
            r"%m": _("MM"),
            r"%d": _("DD"),
            r"%H": _("HH"),
            r"%M": _("MM"),
            r"%S": _("SS"),
        }
        split_format = re.split(r"([.\-/\:\s])", date_format)
        items = [i18n.get(item, item) for item in split_format]
        return format_lazy("{}" * len(items), *items)

    def create_root(self, context):
        root = super().create_root(context)
        root.attrib["placeholder"] = self.date_format_placeholder(root.attrib["format"])
        return root


class FormDataEncoder(DjangoJSONEncoder):
    def default(self, obj):
        try:
            return super().default(self, obj)
        except TypeError:
            return str(obj)


class SelectRenderer(WidgetRenderer):
    tag = "vf-field-select"

    def create_root(self, context):
        root = super().create_root(context)
        root.attrib["optgroups"] = json.dumps(
            [
                {
                    "name": name or "",
                    "options": {
                        key: value
                        for key, value in options[0].items()
                        if key not in ["template_name", "type", "wrap_label"]
                    },
                }
                for name, options, _ in context["widget"]["optgroups"]
            ],
            cls=FormDataEncoder,
        )
        return root


class SelectMultipleRenderer(SelectRenderer):
    tag = "vf-field-select-multiple"


class CheckboxSelectMultipleRenderer(SelectRenderer):
    tag = "vf-field-checkbox-select"


class DependentSelectRenderer(SelectRenderer):
    tag = "vf-field-select-dependent"


class TimeInputRenderer(InputRenderer):
    tag = "vf-field-time"

    def time_format_placeholder(self, time_format):
        i18n = {
            r"%H": _("HH"),
            r"%M": _("MM"),
            r"%S": _("SS"),
            r"%I": _("HH"),
            r"%p": _("AM/PM"),
        }
        split_format = re.split(r"([.\-/\:\s])", time_format)
        items = [i18n.get(item, item) for item in split_format]
        return format_lazy("{}" * len(items), *items)

    def create_root(self, context):
        root = super().create_root(context)

        widget_format = self.bound_field.field.widget.format
        input_format = (
            widget_format if widget_format else self.bound_field.field.input_formats[0]
        )
        root.attrib["format"] = input_format
        root.attrib["placeholder"] = self.time_format_placeholder(input_format)
        return root


class RadioSelectRenderer(SelectRenderer):
    tag = "vf-field-radio-select"


class FormWidgetRenderer(WidgetRenderer):
    tag = "vf-field-form"

    def render(self, template_name, context, request=None):
        root = self.create_root(context)

        wrapper = ElementTree.SubElement(
            root,
            "div",
            {
                "class": "vf-form__formset",
            },
        )
        title = ElementTree.SubElement(
            wrapper,
            "h3",
            {
                "class": "mdc-typography--subheading2 vf-form__formset-header",
            },
        )
        title.text = force_str(self.bound_field.label)

        form = context["widget"]["value"]
        if hasattr(form, "layout"):
            wrapper.append(form.layout.render_form(form))
        else:
            wrapper.append(FormLayout().render_form(form))
        return root


class FormSetWidgetRenderer(WidgetRenderer):
    tag = "vf-field-formset"

    def render_form(self, root: ElementTree.Element, form):
        if isinstance(self.layout_node, FormSet):
            # put the form inside a card
            grid = ElementTree.SubElement(
                root,
                "div",
                {
                    "class": "mdc-layout-grid__cell"
                    f" mdc-layout-grid__cell--span-{self.layout_node.card_desktop}-desktop"
                    f" mdc-layout-grid__cell--span-{self.layout_node.card_tablet}-tablet"
                    f" mdc-layout-grid__cell--span-{self.layout_node.card_mobile}-mobile"
                },
            )
            root = ElementTree.SubElement(
                grid,
                "div",
                {
                    "class": "mdc-card",
                },
            )

        if hasattr(form, "layout"):
            layout = copy(form.layout)
            if "DELETE" in form.fields and "DELETE" not in layout.children:
                layout.children = layout.children[:]
                layout.children.append("DELETE")

            wrapper = ElementTree.SubElement(
                root,
                "div",
                {
                    "class": "vf-form__formset-form",
                },
            )
            wrapper.append(layout.render_form(form))
        else:
            if "DELETE" in form.fields:
                form_layout = Layout(
                    Row(
                        Column(
                            Row(
                                *[
                                    field.name
                                    for field in form.visible_fields()
                                    if field.name != "DELETE"
                                ]
                            ),
                            desktop=10,
                        ),
                        Column("DELETE", desktop=2),
                    )
                )  # if not isinstance(self.layout_node, FormSet) else FormLayout()
            else:
                form_layout = form_layout = Layout(
                    Row(*[field.name for field in form.visible_fields()]),
                )  # if not isinstance(self.layout_node, FormSet) else FormLayout()
            root.append(form_layout.render_form(form))

    def append_form_template(self, root: ElementTree.Element, formset):
        wrapper = ElementTree.SubElement(
            root,
            "script",
            {
                "type": "form-template",
            },
        )
        self.render_form(wrapper, formset.empty_form)

    def render(self, template_name, context, request=None):
        formset = context["widget"]["value"]

        # do not pass whole formset as the attrubute value
        context["widget"]["value"] = None

        root = self.create_root(context)

        wrapper = ElementTree.SubElement(
            root,
            "div",
            {
                "class": "vf-form__formset",
            },
        )
        title = ElementTree.SubElement(
            wrapper,
            "h3",
            {
                "class": "mdc-typography--subheading2 vf-form__formset-header",
            },
        )
        title.text = force_str(self.bound_field.label)

        self.append_form_template(wrapper, formset)

        forms_wrapper_class = "vf-form__formset-forms"
        if isinstance(self.layout_node, FormSet):
            forms_wrapper_class = "mdc-layout-grid__inner vf-form__formset-forms"
        forms_wrapper = ElementTree.SubElement(
            wrapper,
            "div",
            {
                "class": forms_wrapper_class,
            },
        )

        for form in formset:
            self.render_form(forms_wrapper, form)

        wrapper.append(FormLayout().render_form(formset.management_form))

        button = ElementTree.SubElement(
            wrapper,
            "button",
            {
                "class": "mdc-button mdc-button--outlined vf-from__formset-button",
                "style": "width: 100%;margin-bottom: 16px",
            },
        )
        ElementTree.SubElement(button, "i", {"class": "material-icons"}).text = "add"

        return root


class AjaxModelSelectRenderer(InputRenderer):
    tag = "vf-field-autocomplete"

    def create_root(self, context):
        root = super().create_root(context)

        field = self.bound_field.field
        value_label = ""
        try:
            obj = field.to_python(self.bound_field.value())
            if obj is not None:
                value_label = field.label_from_instance(obj)
            if value_label is None:
                value_label = ""
        except ValidationError:
            pass

        root.attrib["type"] = "hidden"
        root.attrib["value-label"] = value_label
        return root


class AjaxMultipleModelSelectRenderer(InputRenderer):
    tag = "vf-field-autocomplete-multi"

    def create_root(self, context):
        root = super().create_root(context)

        field = self.bound_field.field
        initial_values = [
            {
                'value': field.label_from_instance(item),
                'data': {'id': field.prepare_value(item)},
            }
            for item in field.to_python(self.bound_field.value())
        ]
        root.attrib["initial"] = json.dumps(initial_values)
        return root


class FormLayout:
    """Default form layout."""

    def append_non_field_errors(self, form: forms.Form, root: ElementTree.Element):
        errors = form.non_field_errors()
        errors.extend(
            form.error_class(bound_field.errors)
            for bound_field in form.hidden_fields()
            if bound_field.errors
        )

        if errors:
            wrapper = ElementTree.SubElement(root, "div", {"class": "vf-form__errors"})
            for error in errors:
                child = ElementTree.SubElement(
                    wrapper,
                    "div",
                    {
                        "class": "vf-form__error",
                    },
                )
                child.text = str(error)

    def append_hidden_fields(self, form: forms.Form, root: ElementTree.Element):
        hidden_fields = form.hidden_fields()
        if hidden_fields:
            wrapper = ElementTree.SubElement(
                root, "div", {"class": "vf-form__hiddenfields"}
            )
            for bound_field in hidden_fields:
                self.append_field(wrapper, bound_field)

    def append_visible_fields(self, form: forms.Form, root: ElementTree.Element):
        visible_fields = form.visible_fields()
        if visible_fields:
            wrapper = ElementTree.SubElement(
                root, "div", {"class": "vf-form__visiblefields mdc-layout-grid__inner"}
            )
            for bound_field in form.visible_fields():
                container = ElementTree.SubElement(
                    wrapper,
                    "div",
                    {"class": "mdc-layout-grid__cell mdc-layout-grid__cell--span-12"},
                )
                self.append_field(container, bound_field)

    def append_field(
        self,
        root: ElementTree.Element,
        bound_field: forms.BoundField,
        renderer_class=None,
        layout_node=None,
    ):
        if renderer_class is None:
            renderer_class = WidgetRenderer.get_renderer(bound_field.field.widget)

        widget = bound_field.field.widget
        if bound_field.field.localize:
            widget.is_localized = True
        attrs = bound_field.build_widget_attrs({}, widget)
        if bound_field.auto_id and "id" not in widget.attrs:
            attrs.setdefault("id", bound_field.auto_id)

        widget.render(
            name=bound_field.html_name,
            value=bound_field.value(),
            attrs=attrs,
            renderer=renderer_class(root, bound_field, layout_node),
        )

    def render_form(self, form: forms.Form) -> ElementTree.Element:
        root = ElementTree.Element("div", {"class": "vf-form mdc-layout-grid"})
        self.append_non_field_errors(form, root)
        self.append_hidden_fields(form, root)
        self.append_visible_fields(form, root)
        return root

    def render(self, form: forms.Form, default_layout: "FormLayout" = None):
        return ElementTree.tostring(
            self.render_form(form),
            encoding="unicode",
            method="html",
        )


class Layout(FormLayout):
    """Customizable form layout."""

    def __init__(self, *elements, **kwargs):
        self.children = _convert_to_children(elements)
        super().__init__(**kwargs)

    def append_visible_fields(self, form: forms.Form, root: ElementTree.Element):
        wrapper = ElementTree.SubElement(
            root, "div", {"class": "vf-form__visiblefields mdc-layout-grid__inner"}
        )

        Column(*self.children).append(self, form, wrapper)


class LayoutNode(object):
    """Base class for self-rendered nodes."""

    def __init__(self, desktop=AUTO, tablet=AUTO, mobile=AUTO):
        assert desktop == AUTO or 1 <= desktop <= 12
        self.desktop = desktop

        assert tablet == AUTO or 1 <= tablet <= 8
        self.tablet = tablet

        assert mobile == AUTO or 1 <= mobile <= 4
        self.mobile = mobile

    def append(self, layout: FormLayout, form: forms.Form, root: ElementTree.Element):
        raise NotImplementedError("Subclass should override this")


class Column(LayoutNode):
    """Place elements vertically stacked, one under another.

    Example:
        layout = Layout(
            Row(
                Column('first_name', 'last_name', desktop=8, tablet=6)
                'sex_options'
            )
        )
    """

    def __init__(self, *elements, **kwargs):
        self.id_ = kwargs.pop("id_", None)
        self.children = _convert_to_children(elements)
        super().__init__(**kwargs)

    def append(self, layout: FormLayout, form: forms.Form, root: ElementTree.Element):
        if self.children:
            wrapper = ElementTree.SubElement(
                root,
                "div",
                {
                    "class": "vf-form-column mdc-layout-grid__cell mdc-layout-grid__cell--span-12"
                },
            )
            if self.id_:
                wrapper.attrib["id"] = self.id_
            for child in self.children:
                child.append(layout, form, wrapper)


class Row(LayoutNode):
    """Spread elements over a single line.

    Example:

        layout = Layout(
            Row(
                'first_name',
                Row('last_name', 'sex', tablet=5)
            )
        )
    """

    def __init__(self, *elements, **kwargs):
        self.id_ = kwargs.pop("id_", None)
        self.children = _convert_to_children(elements)
        super().__init__(**kwargs)

    def append(self, layout: FormLayout, form: forms.Form, root: ElementTree.Element):
        desktop = _children_sizes(
            [child.desktop for child in self.children],
            grid_size=12,
            grid_name="desktop",
            keep_in_row=True,
        )
        tablet = _children_sizes(
            [child.tablet for child in self.children],
            grid_size=8,
            grid_name="tablet",
            keep_in_row=False,
        )
        mobile = _children_sizes(
            [child.mobile for child in self.children],
            grid_size=4,
            grid_name="mobile",
            keep_in_row=False,
        )

        def append_child(wrapper, child, desktop: int, tablet: int, mobile: int):
            classes = " ".join(
                [
                    "mdc-layout-grid__cell",
                    f"mdc-layout-grid__cell--span-{desktop}-desktop",
                    f"mdc-layout-grid__cell--span-{tablet}-tablet",
                    f"mdc-layout-grid__cell--span-{mobile}-mobile",
                ]
            )

            element = ElementTree.SubElement(
                wrapper,
                "div",
                {
                    "class": classes,
                },
            )
            child.append(layout, form, element)

        wrapper = ElementTree.SubElement(
            root,
            "div",
            {
                "class": "vf-form-row mdc-layout-grid__inner",
            },
        )
        if self.id_:
            wrapper.attrib["id"] = self.id_
        for child_data in zip(self.children, desktop, tablet, mobile):
            append_child(wrapper, *child_data)


class Span(LayoutNode):
    """Span a form field over several columns.

    Example::
        layout = Layout(
            Row(Span('first_name'), Span('last_name'))
            Row(
                Span('email', tablet=6, mobile=3),
                'sex'
            )
        )

    By default span is auto-sized. On a desktop all auto-sized elements
    would be spread equally over the free place of a row, non occupied by
    elements with specific sizes.

    On mobile and tablet if all elements in a row have auto-sizes,
    each element would be placed in a new line. If even one element
    in a row has a specific size, all auto-sized elements would be
    kept in a single line, like on a desktop.

    """

    def __init__(self, field_name, **kwargs):
        self.field_name = field_name
        super().__init__(**kwargs)

    def __str__(self):
        return f"Field {self.field_name} <{self.desktop}, {self.tablet}, {self.mobile}>"

    def append(self, layout: FormLayout, form: forms.Form, root: ElementTree.Element):
        try:
            bound_field = form[self.field_name]
        except KeyError as exc:
            raise ValueError(
                f"{self.field_name} field not found in the {type(form).__name__}"
            ) from exc

        layout.append_field(root, bound_field, layout_node=self)


class Caption(LayoutNode):
    def __init__(self, text, **kwargs):
        self.text = text
        super().__init__(*kwargs)

    def append(self, layout: FormLayout, form: forms.Form, root: ElementTree.Element):
        wrapper = ElementTree.SubElement(
            root,
            "div",
            {
                "class": "vf-form-column mdc-layout-grid__cell mdc-layout-grid__cell--span-12"
            },
        )
        ElementTree.SubElement(
            wrapper,
            "h6",
            {
                "class": "mdc-typography--caption",
                "style": "margin-bottom: 16px;margin-top: 16px;",
            },
        ).text = self.text


class FieldSet(Column):
    def __init__(self, title, *elements, **kwargs):
        self.title = title
        super().__init__(*elements, **kwargs)

    def append(self, layout: FormLayout, form: forms.Form, root: ElementTree.Element):
        wrapper = ElementTree.SubElement(
            root,
            "div",
            {
                "class": "vf-form__formset",
            },
        )
        title = ElementTree.SubElement(
            wrapper,
            "h3",
            {
                "class": "mdc-typography--subheading2 vf-form__formset-header",
            },
        )
        title.text = force_str(self.title)
        super().append(layout, form, wrapper)


class FormSet(Span):
    """Render stacked inline."""

    def __init__(
        self,
        formset_field_name: str,
        card_desktop: int = 12,
        card_tablet: int = 8,
        card_mobile: int = 4,
        **kwargs,
    ):
        assert 1 <= card_desktop <= 12
        self.card_desktop = card_desktop

        assert 1 <= card_tablet <= 8
        self.card_tablet = card_tablet

        assert 1 <= card_mobile <= 4
        self.card_mobile = card_mobile

        super().__init__(formset_field_name, **kwargs)


def _convert_to_children(elements: List[Union[LayoutNode, str]]):
    result = []
    for element in elements:
        if isinstance(element, LayoutNode):
            result.append(element)
        elif isinstance(element, str):
            result.append(Span(element))
        else:
            raise ValueError(f"Unknown element {element} type {type(element)}")
    return result


def _children_sizes(spans, grid_size=12, grid_name="desktop", keep_in_row=True):
    bound = sum(span for span in spans if span != AUTO)
    auto_count = sum(1 for span in spans if span == AUTO)

    if bound == 0 and not keep_in_row:
        # If children AUTO-sized - put every child on the own row
        return [grid_size for _ in spans]
    else:
        rest = grid_size - bound
        if rest < 0 or (auto_count != 0 and grid_size % auto_count) != 0:
            raise ValueError(
                f"Can't equally spread {spans} over {grid_size} columns on a {grid_name} grid"
            )
        return [rest // auto_count if child == AUTO else child for child in spans]


WIDGET_RENDERERS = {
    forms.CheckboxInput: CheckboxRenderer,
    forms.CheckboxSelectMultiple: CheckboxSelectMultipleRenderer,
    forms.DateInput: DateInputRenderer,
    forms.DateTimeInput: DateTimeInputRenderer,
    forms.FileInput: FileInputRenderer,
    forms.HiddenInput: HiddenInputRenderer,
    forms.MultipleHiddenInput: MultipleHiddenInputRenderer,
    forms.PasswordInput: PasswordInputRenderer,
    forms.RadioSelect: RadioSelectRenderer,
    forms.Select: SelectRenderer,
    forms.SelectMultiple: SelectMultipleRenderer,
    forms.Textarea: TextareaRenderer,
    forms.TimeInput: TimeInputRenderer,
}
