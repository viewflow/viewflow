from django import forms


def get_default_form_data(form):
    """
    Given an unbound form, determine what data would
    be generated from POSTing the form unchanged.
    """
    def value_from_widget(initial_value, widget):
        value = initial_value
        if value != '':
            if hasattr(widget, '_format_value'):
                value = widget._format_value(value)
        return value

    data = {}
    for name, field in form.fields.items():
        if isinstance(field.widget, forms.MultiWidget):
            value = field.widget.decompress(form.initial[name])
            for i, widget in enumerate(field.widget.widgets):
                try:
                    widget_value = value[i]
                except IndexError:
                    widget_value = None
                data['%s_%s' % (name, i)] = value_from_widget(widget_value, widget)
        else:
            data[name] = value_from_widget(form.initial[name], field.widget)

    if form.prefix:
        return dict([('%s-%s' % (form.prefix, k), v) for k, v in data.items()])
    else:
        return data
