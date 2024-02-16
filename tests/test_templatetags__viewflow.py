from django.contrib.auth.models import User
from django.template import Template, Context
from django.test import TestCase, RequestFactory, override_settings
from django.urls import path
from viewflow.urls import Site, ModelViewset


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):
    fixtures = ["users.json"]

    def setUp(self):
        self.request = RequestFactory().get("/test/")
        self.user = User.objects.get(username="admin")
        self.request.user = self.user

    def test_get_absolute_url(self):
        context = Context({"request": self.request, "site": site, "user": self.user})
        context.request = self.request

        content = Template(
            "{% load viewflow %}{% get_absolute_url site user %}"
        ).render(context)
        self.assertEqual(f"/user/{self.user.pk}/change/", content)

        content = Template(
            "{% load viewflow %}{% get_absolute_url site user as var%}{{ var }}"
        ).render(context)
        self.assertEqual(f"/user/{self.user.pk}/change/", content)

    def test_reverse(self):
        context = Context(
            {"request": self.request, "viewset": site.viewsets[0], "user": self.user}
        )
        context.request = self.request

        content = Template(
            "{% load viewflow %}{% reverse viewset 'change' user.pk %}"
        ).render(context)
        self.assertEqual(f"/user/{self.user.pk}/change/", content)

        content = Template(
            "{% load viewflow %}{% reverse viewset 'change' user.pk as var %}{{ var }}"
        ).render(context)
        self.assertEqual(f"/user/{self.user.pk}/change/", content)

        content = Template(
            "{% load viewflow %}{% reverse viewset 'change' pk=user.pk %}"
        ).render(context)
        self.assertEqual(f"/user/{self.user.pk}/change/", content)

    def test_get_verbose_name(self):
        context = Context({"model": User})
        content = Template("{% load viewflow %}{{ model|verbose_name }}").render(
            context
        )
        self.assertEqual("user", content)

        context = Context({"user": self.user})
        content = Template("{% load viewflow %}{{ user|verbose_name }}").render(context)
        self.assertEqual("user", content)

    def test_get_verbose_name_plural(self):
        context = Context({"model": User})
        content = Template("{% load viewflow %}{{ model|verbose_name_plural }}").render(
            context
        )
        self.assertEqual("users", content)

        context = Context({"user": self.user})
        content = Template("{% load viewflow %}{{ user|verbose_name_plural }}").render(
            context
        )
        self.assertEqual("users", content)

    def _test_list_column_order(self):
        pass


site = Site(viewsets=[ModelViewset(model=User)])

urlpatterns = [path("", site.urls)]
