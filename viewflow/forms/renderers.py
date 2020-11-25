import json
import re
from typing import List, Type, Union
from functools import lru_cache
from xml.etree import ElementTree

from django import forms
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_str
from django.utils.formats import get_format
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from viewflow.utils import MARKER


AUTO = MARKER('AUTO')


class WidgetRenderer(object):
    tag = 'vf-field-input'

    def __init__(self, root: ElementTree.Element, bound_field: forms.BoundField):
        self.root = root
        self.bound_field = bound_field

    def format_value(self, value):
        if isinstance(value, (tuple, list)):
            return ','.join(f"{item}" for item in value)
        return f"{value}"

    def create_root(self, context):
        attrs = {
            key: str(value) if value is not True else key
            for key, value in context['widget']['attrs'].items()
            if value is not False
        }
        attrs['name'] = context['widget']['name']
        value = context['widget']['value']
        if value is not None:
            attrs['value'] = self.format_value(value)
        if self.bound_field.label:
            attrs['label'] = self.bound_field.label
        if self.bound_field.errors:
            attrs['error'] = self.bound_field.errors[0]
        if self.bound_field.help_text:
            attrs['help-text'] = self.bound_field.help_text
        return ElementTree.SubElement(self.root, self.tag, **attrs)

    def render(self, template_name, context, request=None):
        return self.create_root(context)

    @staticmethod
    @lru_cache(maxsize=None)
    def get_renderer(widget: forms.Widget) -> 'Type[WidgetRenderer]':
        from viewflow.conf import settings
        for widget_class in type(widget).mro()[:-2]:
            try:
                return settings.WIDGET_RENDERERS[widget_class]
            except KeyError:
                continue

        return InputRenderer


class CheckboxRenderer(WidgetRenderer):
    tag = 'vf-field-checkbox'


class InputRenderer(WidgetRenderer):
    def create_root(self, context):
        root = super().create_root(context)
        root.attrib['type'] = context['widget']['type']
        return root


class HiddenInputRenderer(WidgetRenderer):
    tag = 'input'

    def create_root(self, context):
        root = super().create_root(context)
        root.attrib['type'] = 'hidden'
        return root


class PasswordInputRenderer(InputRenderer):
    tag = 'vf-field-password'


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
            wrapper = ElementTree.SubElement(root, 'div', {
                'class': 'vf-form__errors'
            })
            for error in errors:
                child = ElementTree.SubElement(wrapper, 'div', {
                    'class': 'vf-form__error',
                })
                child.text = str(error)

    def append_hidden_fields(self, form: forms.Form, root: ElementTree.Element):
        hidden_fields = form.hidden_fields()
        if hidden_fields:
            wrapper = ElementTree.SubElement(root, 'div', {
                'class': 'vf-form__hiddenfields'
            })
            for bound_field in hidden_fields:
                self.append_field(wrapper, bound_field, HiddenInputRenderer)

    def append_visible_fields(self, form: forms.Form, root: ElementTree.Element):
        visible_fields = form.visible_fields()
        if visible_fields:
            wrapper = ElementTree.SubElement(root, 'div', {
                'class': 'vf-form__visiblefields mdc-layout-grid__inner'
            })
            for bound_field in form.visible_fields():
                container = ElementTree.SubElement(wrapper, 'div', {
                    'class': 'mdc-layout-grid__cell mdc-layout-grid__cell--span-12'
                })
                self.append_field(container, bound_field)

    def append_field(self, root: ElementTree.Element, bound_field: forms.BoundField, renderer_class=None):
        if renderer_class is None:
            renderer_class = WidgetRenderer.get_renderer(bound_field.field.widget)

        widget = bound_field.field.widget
        if bound_field.field.localize:
            widget.is_localized = True
        attrs = bound_field.build_widget_attrs({}, widget)
        if bound_field.auto_id and 'id' not in widget.attrs:
            attrs.setdefault('id', bound_field.auto_id)

        widget.render(
            name=bound_field.html_name,
            value=bound_field.value(),
            attrs=attrs,
            renderer=renderer_class(root, bound_field),
        )

    def render_form(self, form: forms.Form) -> ElementTree.Element:
        root = ElementTree.Element('div', {
            'class': 'vf-form mdc-layout-grid'
        })
        self.append_non_field_errors(form, root)
        self.append_hidden_fields(form, root)
        self.append_visible_fields(form, root)
        return root

    def render(self, form: forms.Form, default_layout: 'FormLayout' = None):
        return ElementTree.tostring(
            self.render_form(form),
            encoding='unicode',
            method='html',
        )


class Layout(FormLayout):
    """Customizable form layout."""
    def __init__(self, *elements, **kwargs):
        self.children = _convert_to_children(elements)
        super().__init__(**kwargs)

    def append_visible_fields(self, form: forms.Form, root: ElementTree.Element):
        wrapper = ElementTree.SubElement(root, 'div', {
            'class': 'vf-form__visiblefields mdc-layout-grid__inner'
        })

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
        self.id_ = kwargs.pop('id_', None)
        self.children = _convert_to_children(elements)
        super().__init__(**kwargs)

    def append(self, layout: FormLayout, form: forms.Form, root: ElementTree.Element):
        if self.children:
            wrapper = ElementTree.SubElement(root, 'div', {
                'class': 'vf-form-column mdc-layout-grid__cell mdc-layout-grid__cell--span-12'
            })
            if self.id_:
                wrapper.attrib['id'] = self.id_
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
        self.id_ = kwargs.pop('id_', None)
        self.children = _convert_to_children(elements)
        super().__init__(**kwargs)

    def append(self, layout: FormLayout, form: forms.Form, root: ElementTree.Element):
        desktop = _children_sizes(
            [child.desktop for child in self.children], grid_size=12,
            grid_name='desktop', keep_in_row=True
        )
        tablet = _children_sizes(
            [child.tablet for child in self.children], grid_size=8,
            grid_name='tablet', keep_in_row=False
        )
        mobile = _children_sizes(
            [child.mobile for child in self.children], grid_size=4,
            grid_name='mobile', keep_in_row=False
        )

        def append_child(wrapper, child, desktop: int, tablet: int, mobile: int):
            classes = ' '.join([
                "mdc-layout-grid__cell",
                f"mdc-layout-grid__cell--span-{desktop}-desktop",
                f"mdc-layout-grid__cell--span-{tablet}-tablet",
                f"mdc-layout-grid__cell--span-{mobile}-mobile"
            ])

            element = ElementTree.SubElement(wrapper, 'div', {
                'class': classes,
            })
            child.append(layout, form, element)

        wrapper = ElementTree.SubElement(root, 'div', {
            'class': "vf-form-row mdc-layout-grid__inner",
        })
        if self.id_:
            wrapper.attrib['id'] = self.id_
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
        return f'Field {self.field_name} <{self.desktop}, {self.tablet}, {self.mobile}>'

    def append(self, layout: FormLayout, form: forms.Form, root: ElementTree.Element):
        try:
            bound_field = form[self.field_name]
        except KeyError as exc:
            raise ValueError(
                f'{self.field_name} field not found in the {type(form).__name__}'
            ) from exc

        layout.append_field(root, bound_field)


class Fieldset(Column):
    def __init__(self, title, *elements, **kwargs):
        self.title = title
        super().__init__(*elements, **kwargs)

    def append(self, layout: FormLayout, form: forms.Form, root: ElementTree.Element):
        wrapper = ElementTree.SubElement(root, 'div', {
            'class': "vf-form__formset",
        })
        title = ElementTree.SubElement(wrapper, 'h3', {
            'class': "mdc-typography--subheading2 vf-form__formset-header",
        })
        title.text = force_str(self.title)
        super().append(layout, form, wrapper)


class Stacked(LayoutNode):
    """Render stacked inline."""
    def __init__(self, *elements, **kwargs):
        self.id_ = kwargs.pop('id_', None)
        self.children = _convert_to_children(elements)
        super().__init__(**kwargs)

    def append(self, layout: FormLayout, form: forms.Form, root: ElementTree.Element):
        """ TODO implement stacked render."""
        # return Div(class_="vf-form-column mdc-layout-grid__cell mdc-layout-grid__cell--span-12", id_=self.id_) / [
        #     child.render(form) for child in self.children
        # ]


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


def _children_sizes(spans, grid_size=12, grid_name='desktop', keep_in_row=True):
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
        return [
            rest // auto_count if child == AUTO else child
            for child in spans
        ]


WIDGET_RENDERERS = {
    forms.CheckboxInput: CheckboxRenderer,
    forms.HiddenInput: HiddenInputRenderer,
    forms.PasswordInput: PasswordInputRenderer,
}
