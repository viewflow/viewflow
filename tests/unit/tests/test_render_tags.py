from django.template import Template, Context
from django.test import TestCase
from unit.forms import AllElementsForm


class TestRenderTag(TestCase):
    DEFAULT_RENDER_TEMPLATE = """
        {% load viewflow %}
        {% viewform 'viewflow/form/layout.html' %}
            {% viewpart field 'text_input' %}
            REDEFINED
            {% endviewpart %}
        {% endviewform %}
    """

    def test_render_form_succeed(self):
        template = Template(TestRenderTag.DEFAULT_RENDER_TEMPLATE)
        result = template.render(Context({'form': AllElementsForm()}))
        self.assertIn('REDEFINED', result)
