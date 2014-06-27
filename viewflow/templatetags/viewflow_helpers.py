import re
from django import template

register = template.Library()


def replace_all(repls, str):
    return re.sub('|'.join(re.escape(key) for key in repls.keys()), lambda k: repls[k.group(0)], str)


@register.filter
def input_mask(bound_field):
    """
    Returns firts field date input format in jquery.inputmask compatible way
    """
    input_format = bound_field.field.input_formats[0]
    return replace_all({"%d": "dd", "%m": "mm", '%Y': 'yyyy'}, input_format)
