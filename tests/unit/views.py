from django.views.generic.edit import FormView
from unit.forms import AllElementsForm
from viewflow.site import Layout, Fieldset, Row, Column, Span2


class TestFormView(FormView):
    template_name = 'unit/form.html'
    form_class = AllElementsForm
    layout = Layout(
        Row(
            Fieldset(
                "Basic fields",
                Row(Column('text_input', 'email_field', 'boolean_checkbox'),
                    'textarea_input'),
                Row(Column('date_field',
                           'datetime_field',
                           'time_field'),
                    Column('integer_field', 'float_field', 'decimal_field'))),
            Fieldset(
                "Choice fields",
                Row('choices_radio_field',
                    Column('choices_field',
                           'multiplechoice_field',
                           'nullboolean_field')))),
        Row(
            Fieldset(
                'File fields',
                Row('file_field', 'image_field', Span2('filepath_field'))),
            Fieldset(
                'Other',
                Row('ipaddress_field', 'generic_ipaddress_field'),
                Row('regex_field', 'slug_field', Span2('url_field')),
                #Row('combo_field'),
                #Row('splitdatetime_field')
            )))
