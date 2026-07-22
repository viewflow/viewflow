from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import path
from viewflow.urls import DeleteViewMixin, ModelViewset


class UserViewset(DeleteViewMixin, ModelViewset):
    model = User
    list_columns = ("username", "email")
    # NOTE: no list_filterset_class / list_filter_fields configured


class ScopedUserViewset(DeleteViewMixin, ModelViewset):
    model = User
    list_columns = ("username", "email")

    def get_queryset(self, request):
        # request-scoped queryset (e.g. account isolation)
        return User.objects.filter(is_staff=True)


viewset = UserViewset()
scoped_viewset = ScopedUserViewset()

urlpatterns = [
    path("users/", viewset.urls),
    path("scoped/", scoped_viewset.urls),
]


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@admin.com", "admin")
        self.assertTrue(self.client.login(username="admin", password="admin"))

    def test_bulk_delete_select_all_without_filterset_does_not_500(self):
        # A viewset without a configured filterset leaves
        # FilterableViewMixin.get_queryset with self.filterset = None. The
        # "Select All" branch of objects_count read self.filterset.form,
        # crashing with AttributeError: 'NoneType' object has no attribute
        # 'form'.
        User.objects.create_user("bob", "bob@example.com", "pwd")
        count_before = User.objects.count()

        response = self.client.post(
            "/users/action/delete/",
            {"select_all": "on", "action": "delete"},
        )

        # confirmation page (not confirmed yet), not a crash
        self.assertEqual(response.status_code, 200)
        # nothing deleted before confirmation
        self.assertEqual(User.objects.count(), count_before)

    def test_bulk_delete_select_all_confirmed_deletes_all(self):
        User.objects.create_user("bob", "bob@example.com", "pwd")

        response = self.client.post(
            "/users/action/delete/",
            {"select_all": "on", "action": "delete", "_confirm": "1"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.count(), 0)

    def test_bulk_delete_select_all_respects_viewset_get_queryset(self):
        # "Select All" must stay within the viewset's scope: only the staff
        # user (admin) is in scope, the plain user must survive.
        bob = User.objects.create_user("bob", "bob@example.com", "pwd")

        response = self.client.post(
            "/scoped/action/delete/",
            {"select_all": "on", "action": "delete", "_confirm": "1"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(pk=bob.pk).exists())
        self.assertFalse(User.objects.filter(pk=self.admin.pk).exists())
