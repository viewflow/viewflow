from django.test import TestCase
from viewflow import utils


class Test(TestCase):  # noqa: D101
    def test_get_app_package_succeed(self):
        self.assertEqual(utils.get_app_package('admin'), 'django.contrib.admin')
        self.assertEqual(utils.get_app_package('auth'), 'django.contrib.auth')
        self.assertEqual(utils.get_app_package('viewflow'), 'viewflow.workflow')

    def test_get_app_package_bug112(self):
        """ Application models are located in a module that consists of multiple files """
        self.assertEqual(utils.get_app_package('tests'), 'tests')

    def test_get_app_package_missing_app_raise(self):
        self.assertRaises(Exception, utils.get_app_package, 'missing_app')

    def test_get_containing_app_data_succeed(self):
        self.assertEqual(utils.get_containing_app_data('django.contrib.admin.views'),
                         ('admin', 'django.contrib.admin'))
        self.assertEqual(utils.get_containing_app_data('django.contrib.auth.urls'),
                         ('auth', 'django.contrib.auth'))
        self.assertEqual(utils.get_containing_app_data('viewflow.workflow.flow'),
                         ('viewflow', 'viewflow.workflow'))

    def test_get_containing_app_data_bug112(self):
        """ Application models are located in a module that consists of multiple files """
        self.assertEqual(utils.get_containing_app_data('tests.models'),
                         ('tests', 'tests'))

    def test_get_containing_app_data_none_on_missing(self):
        self.assertEqual(utils.get_containing_app_data('unknown.module'),
                         (None, None))
