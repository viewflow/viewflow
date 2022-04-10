from django.urls import path
from django.test import TestCase, override_settings
from viewflow.contrib.admin import Admin
from viewflow.urls import Site


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):
    fixtures = ['users.json']

    def test_admin_viewset_entry(self):
        self.assertTrue(self.client.login(username='admin', password='admin'))

        response = self.client.get('/')
        self.assertRedirects(response, '/admin/')


urlpatterns = [
    path('', Site(viewsets=[Admin()]).urls)
]
