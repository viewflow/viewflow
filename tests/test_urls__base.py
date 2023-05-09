from django.views.generic import TemplateView
from django.urls import path, reverse
from django.test import TestCase, override_settings
from viewflow.urls import route, IndexViewMixin, Viewset


class NestedViewset(IndexViewMixin, Viewset):
    app_name = "nested"

    page_path = path(
        "page/", TemplateView.as_view(template_name="viewflow/base.html"), name="page"
    )
    route_path = route("test/", Viewset())


class InheritedViewset(NestedViewset):
    app_name = "nested"

    page_path = path(
        "page2/", TemplateView.as_view(template_name="viewflow/base.html"), name="page"
    )


class RootViewset(Viewset):
    app_name = "root"

    index_path = path(
        "", TemplateView.as_view(template_name="viewflow/base.html"), name="index"
    )
    nested_path = route("test/", NestedViewset())
    nested2_path = route("nested2/", NestedViewset(app_name="nested2"))

    # check here that route_url mounted second time successfully
    nested3_path = route("inherited/", InheritedViewset(app_name="nested2"))


urlconfig = RootViewset()

urlpatterns = [path("", urlconfig.urls)]


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):  # noqa: D101
    def test_created_urls(self):
        self.assertEqual("/", reverse("root:index"))

        self.assertEqual("/test/", reverse("root:nested:index"))
        self.assertEqual("/test/page/", reverse("root:nested:page"))

        self.assertEqual("/nested2/", reverse("root:nested2:index"))
        self.assertEqual("/nested2/page/", reverse("root:nested2:page"))

    def test_urlconf_resolve(self):
        self.assertEqual("/", urlconfig.reverse("index"))
        self.assertEqual("/test/", urlconfig.nested_path.viewset.reverse("index"))
        self.assertEqual("/test/page/", urlconfig.nested_path.viewset.reverse("page"))

    def test_auto_redirect(self):
        response = self.client.get(reverse("root:nested:index"))
        self.assertRedirects(response, "/test/page/")
