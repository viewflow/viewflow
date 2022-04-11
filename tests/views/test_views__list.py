from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import path
from viewflow.views import ListModelView


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):  # noqa: D101
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@admin.com", "admin")
        self.assertTrue(self.client.login(username="admin", password="admin"))

    def test_generic_list_view(self):
        response = self.client.get("/user/")
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<td class="vf-list__table-cell-text">admin@admin.com</td>',
            str(response.content),
        )

    def test_advance_list_view(self):
        response = self.client.get("/advanced_user/")
        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<td class="vf-list__table-cell-text">Admin</td>',
            str(response.content),
        )

        response = self.client.get("/advanced_user/?_orderby=first_name")
        self.assertIn('data-list-sort-column="last_name"', str(response.content))


class UserListView(ListModelView):
    model = User
    columns = (
        "first_name",
        "last_name",
        "email",
        "get_full_name",
        "role",
    )
    ordering = "pk"

    def role(self, obj):
        return "Admin" if obj.is_superuser else "User"


urlpatterns = [
    path(
        "user/",
        ListModelView.as_view(
            model=User,
            columns=("first_name", "last_name", "email", "is_staff"),
            ordering="pk",
        ),
    ),
    path("advanced_user/", UserListView.as_view()),
]
