from django.test import TestCase
from django.forms.fields import DateTimeField
from viewflow.site.templatetags import viewform


class TestDatePickerFormatFilter(TestCase):
    def test_format_translation(self):
        translations = {
            '%Y-%m-%d': 'yyyy-mm-dd',
            '%m/%d/%Y': 'mm/dd/yyyy',
            '%m/%d/%y': 'mm/dd/yy',
            '%b %d %Y': 'M dd yyyy',
            '%b %d, %Y': 'M dd, yyyy',
            '%d %b %Y': 'dd M yyyy',
            '%d %b, %Y': 'dd M, yyyy',
            '%B %d %Y': 'MM dd yyyy',
            '%B %d, %Y': 'MM dd, yyyy',
            '%d %B %Y': 'dd MM yyyy',
            '%d %B, %Y': 'dd MM, yyyy',
            '%Y-%m-%d %H:%M:%S': 'yyyy-mm-dd hh:ii:ss',
            '%Y-%m-%d %H:%M': 'yyyy-mm-dd hh:ii',
            '%m/%d/%Y %H:%M:%S': 'mm/dd/yyyy hh:ii:ss',
            '%m/%d/%Y %H:%M': 'mm/dd/yyyy hh:ii',
            '%m/%d/%y %H:%M:%S': 'mm/dd/yy hh:ii:ss',
            '%m/%d/%y %H:%M': 'mm/dd/yy hh:ii',
        }

        for input_format, output_format in translations.items():
            field = DateTimeField(input_formats=[input_format])
            result = viewform.datepicker_format(field)
            self.assertEqual(output_format, result)
