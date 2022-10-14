import html5lib
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import render
from django.test import RequestFactory, TestCase, override_settings
from django.urls import path
from django.views.generic import TemplateView
from viewflow.urls import Application, AppMenuMixin, IndexViewMixin, Site, Viewset


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):
    fixtures = ['users.json']

    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = AnonymousUser()
        self.validator = html5lib.HTMLParser(strict=True)

    def test_base(self):
        response = render(self.request, 'viewflow/base.html', {})
        self.validator.parse(response.content)

    def test_base__snackbar(self):
        response = render(self.request, 'viewflow/base.html', {
            'messages': ['Test message 1', 'Rest message 2']
        })
        self.assertTrue('vf-snackbar' in response.content.decode())
        self.validator.parse(response.content)

    def test_base_page(self):
        response = render(self.request, 'viewflow/base_page.html', {})
        self.validator.parse(response.content)

    def test_base_page__with_site_menu(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get('/application/test/test/')
        self.assertTrue('Test Application' in response.content.decode())
        self.assertTrue('Test Viewset' in response.content.decode())
        self.validator.parse(response.content)

    def test_lockscreen__404(self):
        response = render(self.request, '404.html', {})
        self.validator.parse(response.content)


class TestViewset(IndexViewMixin, AppMenuMixin, Viewset):
    title = 'Test Viewset'
    page_path = path('test/', TemplateView.as_view(template_name='viewflow/base_page.html'), name="page")


urlpatterns = [
    path('', Site(viewsets=[
        Application(
            title='Test Application',
            viewsets=[TestViewset()]
        )
    ]).urls)
]
