import os
from datetime import datetime
from django import forms
from django.conf import settings


class AllElementsForm(forms.Form):
    boolean_checkbox = forms.BooleanField()
    text_input = forms.CharField(help_text="Sample text input", max_length=50, min_length=10)
    textarea_input = forms.CharField(help_text="Sample textarea", max_length=50, min_length=10, widget=forms.Textarea)
    choices_field = forms.ChoiceField(choices=((('1', 'One'), ('2', 'Two'), ('3', 'Three'))))
    choices_radio_field = forms.ChoiceField(choices=((('1', 'One'), ('2', 'Two'), ('3', 'Three'))),
                                            widget=forms.RadioSelect)
    date_field = forms.DateField(input_formats=['%d.%m.%Y'], initial=datetime.now())
    datetime_field = forms.DateTimeField(input_formats=['%d.%m.%Y %H:%M'], initial=datetime.now())
    decimal_field = forms.DecimalField(max_value=100, min_value=10, max_digits=5, decimal_places=2)
    email_field = forms.EmailField(min_length=5, max_length=50)
    file_field = forms.FileField(max_length=250, help_text='Attach any file here')
    filepath_field = forms.FilePathField(path=os.path.join(settings.BASE_DIR, 'tests/templates'), recursive=True)
    float_field = forms.FloatField(min_value=10, max_value=100)
    image_field = forms.ImageField()
    integer_field = forms.IntegerField(min_value=10, max_value=100)
    ipaddress_field = forms.IPAddressField()
    generic_ipaddress_field = forms.GenericIPAddressField(protocol='IPv6')
    multiplechoice_field = forms.MultipleChoiceField((('1', 'One'), ('2', 'Two'), ('3', 'Three'),
                                                      ('4', 'Four'), ('5', 'Five'), ('6', 'Siz')))
    nullboolean_field = forms.NullBooleanField()
    regex_field = forms.RegexField(regex='[a-zA-Z]+')
    slug_field = forms.SlugField()
    time_field = forms.TimeField(input_formats=['%H:%M'], initial=datetime.now())
    url_field = forms.URLField(min_length=10, max_length=100)
    combo_field = forms.ComboField(fields=[forms.CharField(max_length=20), forms.EmailField()])
    splitdatetime_field = forms.SplitDateTimeField(input_date_formats=['%d.%m.%Y'], input_time_formats=['%H:%M'])
