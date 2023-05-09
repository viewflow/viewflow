from django.test import TestCase, override_settings
from django.urls import path
from django.views.generic import TemplateView
from viewflow.urls import AppMenuMixin, Application, Site, Viewset, route


class NestedViewset(Viewset):
    app_name = "nested"
    page_path = path(
        "page/", TemplateView.as_view(template_name="viewflow/base.html"), name="page"
    )


class CityViewset(AppMenuMixin, Viewset):
    index_path = path(
        "", TemplateView.as_view(template_name="viewflow/base.html"), name="index"
    )
    nested_path = route("nested/", NestedViewset())


site = Site(
    title="Test site",
    viewsets=[
        Application(
            app_name="test",
            viewsets=[
                CityViewset(),
            ],
        )
    ],
)

urlpatterns = [path("", site.urls)]


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):
    def test_context_injected(self):
        response = self.client.get("/test/city/")
        match = response.wsgi_request.resolver_match

        self.assertTrue(hasattr(match, "site"))
        self.assertEqual(match.site, site)

        self.assertTrue(hasattr(match, "app"))
        self.assertEqual(match.app, site._children[0])

        # App -> Site -> CityViewset
        self.assertTrue(hasattr(match, "viewset"))
        self.assertEqual(match.viewset, site._children[0]._children[0])

    def test_nested_viewset_injected(self):
        response = self.client.get("/test/city/nested/page/")
        match = response.wsgi_request.resolver_match

        # App -> Site -> CityViewset -> Nested
        self.assertTrue(hasattr(match, "viewset"))
        self.assertEqual(
            match.viewset, site._children[0]._children[0].nested_path.viewset
        )
