from django.template import Library
from django.contrib.admin.templatetags.base import InclusionAdminNode

register = Library()


@register.tag(name='change_form_fsm_tools')
def change_form_fsm_tag(parser, token):
    """Display the row of fsm actions in object tools."""
    return InclusionAdminNode(
        parser, token,
        func=lambda context: context,
        template_name='fsm_change_form_object_tools.html',
    )
