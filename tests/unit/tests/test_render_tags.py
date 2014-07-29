from django.template import Template, Context
from django.test import TestCase
from ..forms import AllElementsForm


class TestRenderTag(TestCase):
    DEFAULT_RENDER_TEMPLATE = """
        {% load viewform %}
        {% viewform 'viewflow/form/bootstrap3/form.html' form=form layout=view.layout %}
            {% viewpart form.text_input.field %}
                REDEFINED
            {% endviewpart %}
        {% endviewform %}
    """

    def test_render_form_succeed(self):
        template = Template(TestRenderTag.DEFAULT_RENDER_TEMPLATE)
        result = template.render(Context({'form': AllElementsForm()}))
        self.assertIn('REDEFINED', result)
