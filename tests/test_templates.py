import html5lib
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase, override_settings
from django.shortcuts import render


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):
    def setUp(self):
        self.request = RequestFactory().get('/')
        self.request.user = AnonymousUser()
        self.validator = html5lib.HTMLParser(strict=True)

    def test__base(self):
        response = render(self.request, 'viewflow/base.html', {})
        self.validator.parse(response.content)

    def test__base_page(self):
        response = render(self.request, 'viewflow/base_page.html', {})
        self.validator.parse(response.content)

    def test__404(self):
        response = render(self.request, '404.html', {})
        self.validator.parse(response.content)


urlpatterns = [
]
