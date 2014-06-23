from django.template import Template, Context
from django.test import TestCase


class TestRenderTag(TestCase):
    DEFAULT_RENDER_TEMPLATE = """
        {% load viewflow %}
        {% viewform 'unit/test_render_form.html' %}
            {% viewpart field 'username' %}
            REDEFINED
            {% endviewpart %}
        {% endviewform %}
    """

    def test_render_form_succeed(self):
        """
                       

        """
        template = Template(TestRenderTag.DEFAULT_RENDER_TEMPLATE)
        result = template.render(Context({'var': 'varvalue'}))
        self.assertIn('REDEFINED', result)
