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


@render_widget.register(widgets.SelectMultiple)  # NOQA
def _(widget, context, bound_field, attrs=None):
    return render_widget_template(
        context,
        bound_field,
        template_name='viewflow/form/widgets/text_input.html',
        attrs=attrs)
