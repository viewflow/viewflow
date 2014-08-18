from django.core.urlresolvers import reverse
from django.test import TestCase


class AllProcessViewTests(TestCase):
    fixtures = ['helloworld/default_data.json']

    def setUp(self):
        self.assertTrue(self.client.login(username='admin', password='admin'))
        self.base_url = reverse('viewflow_site:index')

    def test_render_succeed(self):
        response = self.client.get(self.base_url)
        self.assertEqual(200, response.status_code)


class AllTasksViewTests(TestCase):
    fixtures = ['helloworld/default_data.json']

    def setUp(self):
        self.assertTrue(self.client.login(username='admin', password='admin'))
        self.base_url = reverse('viewflow_site:tasks')

    def test_render_succeed(self):
        response = self.client.get(self.base_url)
        self.assertEqual(200, response.status_code)


class AllQueueViewTests(TestCase):
    fixtures = ['helloworld/default_data.json']

    def setUp(self):
        self.assertTrue(self.client.login(username='admin', password='admin'))
        self.base_url = reverse('viewflow_site:queue')

    def test_render_succeed(self):
        response = self.client.get(self.base_url)
        self.assertEqual(200, response.status_code)
