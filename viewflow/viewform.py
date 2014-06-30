import warnings
from functools import partial
from singledispatch import singledispatch
from django.forms import widgets
from django.template.loader import get_template


def render_widget_template(context, bound_field, template_name, widget=None, attrs=None):
    """
    Renders field depends on widget template
    """
    if widget is None:
        widget = bound_field.field.widget

    if bound_field.field.localize:
        widget.is_localized = True

    attrs = attrs or {}
    auto_id = bound_field.auto_id

    if auto_id and 'id' not in attrs and 'id' not in widget.attrs:
        attrs['id'] = auto_id

    hidden_initial = ''
    if bound_field.field.show_hidden_initial:
        hidden_initial = bound_field.as_hidden(only_initial=True)

    template = get_template(template_name)
    with context.push({
            'field': bound_field,
            'widget': widget,
            'id': auto_id,
            'hidden_initial': hidden_initial}):
        return template.render(context)


@singledispatch
def render_widget(widget, context, bound_field, attrs=None):
    result = bound_field.as_widget(attrs=attrs)
    if bound_field.field.show_hidden_initial:
        result += bound_field.as_hidden(only_initial=True, attrs=attrs)
    return result


@render_widget.register(widgets.TextInput)
def _(widget, context, bound_field, attrs=None):
    return render_widget_template(
        context,
        bound_field,
        template_name='viewflow/form/widgets/text_input.html',
        attrs=attrs)


@render_widget.register(widgets.Textarea)  # NOQA
def _(widget, context, bound_field, attrs=None):
    return render_widget_template(
        context,
        bound_field,
        template_name='viewflow/form/widgets/textarea.html',
        attrs=attrs)


@render_widget.register(widgets.CheckboxInput)  # NOQA
def _(widget, context, bound_field, attrs=None):
    return render_widget_template(
        context,
        bound_field,
        template_name='viewflow/form/widgets/checkbox.html',
        attrs=attrs)


@render_widget.register(widgets.DateInput)  # NOQA
def _(widget, context, bound_field, attrs=None):
    return render_widget_template(
        context,
        bound_field,
        template_name='viewflow/form/widgets/date_input.html',
        attrs=attrs)


@render_widget.register(widgets.DateTimeInput)  # NOQA
def _(widget, context, bound_field, attrs=None):
    return render_widget_template(
        context,
        bound_field,
        template_name='viewflow/form/widgets/datetime_input.html',
        attrs=attrs)


@render_widget.register(widgets.Select)  # NOQA
def _(widget, context, bound_field, attrs=None):
    return render_widget_template(
        context,
        bound_field,
        template_name='viewflow/form/widgets/select.html',
        attrs=attrs)


@render_widget.register(widgets.RadioSelect)  # NOQA
def _(widget, context, bound_field, attrs=None):
    return render_widget_template(
        context,
        bound_field,
        template_name='viewflow/form/widgets/radio_select.html',
        attrs=attrs)


@render_widget.register(widgets.FileInput)  # NOQA
def _(widget, context, bound_field, attrs=None):
    return render_widget_template(
        context,
        bound_field,
        template_name='viewflow/form/widgets/file_input.html',
        attrs=attrs)


@render_widget.register(widgets.SelectMultiple)  # NOQA
def _(widget, context, bound_field, attrs=None):
    return render_widget_template(
        context,
        bound_field,
        template_name='viewflow/form/widgets/select_multiple.html',
        attrs=attrs)


class Layout(object):
    """
    Declarative management for form layouts
    """
    template_name = 'viewflow/form/layout/layout.html'

    def __init__(self, *elements):
        self.elements = elements

    def __iter__(self):
        for element in self.elements:
            if isinstance(element, str):
                yield Field(element)
            else:
                yield element


class Fieldset(object):
    span_columns = 1
    template_name = 'viewflow/form/layout/fieldset.html'

    def __init__(self, label, *elements):
        self.label = label
        self.elements = elements

    def __iter__(self):
        for element in self.elements:
            if isinstance(element, str):
                yield Field(element)
            else:
                yield element


class Row(object):
    template_name = 'viewflow/form/layout/row.html'

    def __init__(self, *elements):
        self.elements = []
        for element in elements:
            if isinstance(element, str):
                self.elements.append(Field(element))
            else:
                self.elements.append(element)

    def __iter__(self):
        total_span = sum(element.span_columns for element in self.elements)
        if 12 % total_span != 0:
            warnings.warn("Can't equally divide row columns for {}".format(self.elements))

        span_multiplier = 12//total_span
        for element in self.elements:
            yield element, element.span_columns * span_multiplier


class Column(object):
    span_columns = 1
    template_name = 'viewflow/form/layout/column.html'

    def __init__(self, *elements):
        self.elements = elements

    def __iter__(self):
        for element in self.elements:
            if isinstance(element, str):
                yield Field(element)
            else:
                yield element


class Span(object):
    template_name = 'viewflow/form/layout/field.html'

    def __init__(self, span_columns, name):
        self.span_columns = span_columns
        self.name = name


Field = partial(Span, 1)
Span2 = partial(Span, 2)
Span3 = partial(Span, 3)
Span4 = partial(Span, 4)
Span5 = partial(Span, 5)
Span6 = partial(Span, 6)
Span7 = partial(Span, 7)
Span8 = partial(Span, 8)
Span9 = partial(Span, 9)
Span10 = partial(Span, 10)
Span11 = partial(Span, 11)
Span12 = partial(Span, 12)
