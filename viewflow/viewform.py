from singledispatch import singledispatch
from django.forms import widgets
from django.template import Context
from django.template.loader import get_template


def render_widget_template(bound_field, template_name, widget=None, attrs=None):
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
    return template.render(Context({
        'field': bound_field,
        'widget': widget,
        'id': auto_id,
        'hidden_initial': hidden_initial
    }))


@singledispatch
def render_widget(widget, bound_field, attrs=None):
    result = bound_field.as_widget(attrs=attrs)
    if bound_field.field.show_hidden_initial:
        result += bound_field.as_hidden(only_initial=True, attrs=attrs)
    return result


@render_widget.register(widgets.TextInput)
def _(widget, bound_field, template_name='viewflow/form/widgets/text_input.html', attrs=None):
    return render_widget_template(bound_field, template_name=template_name, attrs=attrs)


@render_widget.register(widgets.Textarea)  # NOQA
def _(widget, bound_field, template_name='viewflow/form/widgets/text_input.html', attrs=None):
    return render_widget_template(bound_field, template_name=template_name, attrs=attrs)


@render_widget.register(widgets.CheckboxInput)  # NOQA
def _(widget, bound_field, template_name='viewflow/form/widgets/text_input.html', attrs=None):
    return render_widget_template(bound_field, template_name=template_name, attrs=attrs)


@render_widget.register(widgets.Select)  # NOQA
def _(widget, bound_field, template_name='viewflow/form/widgets/text_input.html', attrs=None):
    return render_widget_template(bound_field, template_name=template_name, attrs=attrs)


@render_widget.register(widgets.RadioSelect)  # NOQA
def _(widget, bound_field, template_name='viewflow/form/widgets/text_input.html', attrs=None):
    return render_widget_template(bound_field, template_name=template_name, attrs=attrs)


@render_widget.register(widgets.SelectMultiple)  # NOQA
def _(widget, bound_field, template_name='viewflow/form/widgets/text_input.html', attrs=None):
    return render_widget_template(bound_field, template_name=template_name, attrs=attrs)
