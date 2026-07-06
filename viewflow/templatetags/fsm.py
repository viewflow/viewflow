import inspect

from django.template import Library
from django.contrib.admin.templatetags.base import InclusionAdminNode

register = Library()


@register.tag(name="change_form_fsm_tools")
def change_form_fsm_tag(parser, token):
    """Display the row of fsm actions in object tools."""
    kwargs = dict(
        func=lambda context: context,
        template_name="fsm_change_form_object_tools.html",
    )
    # Django 5.2 added a required first positional ``name`` argument to
    # InclusionAdminNode; keep working on both older and newer Django.
    if "name" in inspect.signature(InclusionAdminNode.__init__).parameters:
        return InclusionAdminNode("change_form_fsm_tools", parser, token, **kwargs)
    return InclusionAdminNode(parser, token, **kwargs)
