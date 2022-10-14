from django.test import TestCase
from viewflow.workflow.context import context, Context


class Test(TestCase):
    def test_activation_context_scope(self):
        with Context(first_scope='first_scope'):
            with Context(second_scope='second_scope'):
                self.assertEqual(context.first_scope, 'first_scope')
                self.assertEqual(context.second_scope, 'second_scope')

            self.assertEqual(context.first_scope, 'first_scope')
            self.assertTrue(hasattr(context, 'first_scope'))
            self.assertFalse(hasattr(context, 'second_scope'))

        self.assertFalse(hasattr(context, 'first_scope'))
        self.assertFalse(hasattr(context, 'second_scope'))
