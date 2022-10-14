from django.test import TestCase
from viewflow import viewprop


class Viewset(object):  # noqa : D101
    def __init__(self, view=None):
        if view is not None:
            self.view = view

    @viewprop
    def view(self):
        return 'default'


class Test(TestCase):  # noqa: D101
    def test_default_viewprop_value(self):
        viewset = Viewset()
        self.assertEqual(viewset.view, 'default')

    def test_redefine_viewprop_succeed(self):
        viewset = Viewset(view='new value')
        self.assertEqual(viewset.view, 'new value')
