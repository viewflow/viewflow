import os
import re
from collections import defaultdict

from django import template
from django.template.loader import get_template

from tag_parser import template_tag
from tag_parser.basetags import BaseNode
from tag_parser.parser import parse_token_kwargs

from ..viewform import Field


register = template.Library()


class BaseContainerNode(BaseNode):
    def __init__(self, tag_name, nodelist, *args, **kwargs):
        self.nodelist = nodelist
        super(BaseContainerNode, self).__init__(tag_name, *args, **kwargs)

    @classmethod
    def parse(cls, parser, token):
        """
        Parse the tag, instantiate the class.
        """
        tag_name, args, kwargs = parse_token_kwargs(
            parser, token,
            allowed_kwargs=cls.allowed_kwargs,
            compile_args=cls.compile_args,
            compile_kwargs=cls.compile_kwargs
        )
        cls.validate_args(tag_name, *args, **kwargs)

        nodelist = parser.parse(('end{}'.format(tag_name),))
        parser.delete_first_token()
        return cls(tag_name, nodelist, *args, **kwargs)


@template_tag(register, 'viewform')
class ViewFormNode(BaseContainerNode):
    max_args = 1
    allowed_kwargs = ('form', 'layout')

    def render_tag(self, context, template_name, form=None, layout=None):
        template = get_template(template_name)

        if form is None:
            form = context['form']

        if layout is None:
            if 'view' in context:
                view = context['view']
                if hasattr(view, 'layout'):
                    layout = view.layout
        if layout is None:
            if hasattr(form, 'layout'):
                layout = form.layout

        parts = defaultdict(dict)  # part -> section -> value

        with context.push({
                'form': form,
                'layout': layout,
                '_viewform_template_pack': os.path.dirname(template_name),
                '_viewform_parts': parts}):

            children = (node for node in self.nodelist if isinstance(node, ViewPartNode))
            for partnode in children:
                value = partnode.render(context)
                context['_viewform_parts'][partnode.resolve_part(context)][partnode.section] = value

            return template.render(context)


@template_tag(register, 'viewpart')
class ViewPartNode(BaseContainerNode):
    max_args = 2

    def __init__(self, tag_name, nodelist, part_id, section=None):
        self.part_id = part_id
        self.section = section.token if section else None
        super(ViewPartNode, self).__init__(tag_name, nodelist)

    def resolve_part(self, context):
        return self.part_id.resolve(context)

    def render_tag(self, context):
        part = self.resolve_part(context)

        if self.section in context['_viewform_parts'][part]:
            return context['_viewform_parts'][part][self.section]

        children = (node for node in self.nodelist if isinstance(node, ViewPartNode))
        for partnode in children:
            value = partnode.render(context)
            part = partnode.resolve_part(context)

            if partnode.section not in context['_viewform_parts'][part]:
                context['_viewform_parts'][part][partnode.section] = value

        value = self.nodelist.render(context)
        if not value.strip():
            return ''
        return value


@template_tag(register, 'viewfield')
class ViewFieldNode(BaseNode):
    """
    Helper tag, for the case of render form field when we have no layout

    Usage:

        {% viewfield field template='widgets/textinput.html' %}
    """
    max_args = 1
    allowed_kwargs = ('template', )

    def render_tag(self, context, field, template=None):
        context_kwargs = {}
        if template:
            context_kwargs[template] = template

        with context.push(context_kwargs):
                return Field(field.name).render(context)


@template_tag(register, 'tagattrs')
class CssClassNode(BaseContainerNode):
    def render_tag(self, context):
        value = self.nodelist.render(context)
        return re.sub('[\n ]+', ' ', value).strip()
