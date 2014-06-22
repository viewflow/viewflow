from singledispatch import singledispatch
from django.forms import widgets


@singledispatch
def render_widget(widget, name, value, attrs=None):
    return widdget.render(name, value, attrs=attrs)


@render_widget.register(widgets.TextInput)
def _(widget, name, value, attrs=None):
    pass

@render_widget.register(widgets.Textarea)
def _(widget, name, value, attrs=None):
    pass


@render_widget.register(widgets.CheckboxInput)
def _(widget, name, value, attrs=None):
    pass


@render_widget.register(widgets.Select)
def _(widget, name, value, attrs=None):
    pass


@render_widget.register(widgets.RadioSelect)
def _(widget, name, value, attrs=None):
    pass


@render_widget.register(widgets.SelectMultiple)
def _(widget, name, value, attrs=None):
    pass



