import gc
import weakref
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import path
from viewflow.views import ListModelView
from viewflow.views.list import BaseListModelView


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

    def test_search_on_list_view_without_search_fields_does_not_500(self):
        # SearchableViewMixin.search_fields defaults to None (UserListView
        # never sets it), so a client-supplied ?_search= must be a no-op
        # rather than a crash.
        response = self.client.get("/user/?_search=admin")

        self.assertEqual(response.status_code, 200)

    def test_search_filters_when_search_fields_is_set(self):
        User.objects.create_user("nobody", "nobody@example.com", "pwd")

        response = self.client.get("/searchable_user/?_search=admin")

        self.assertEqual(response.status_code, 200)
        self.assertInHTML(
            '<td class="vf-list__table-cell-text">admin@admin.com</td>',
            str(response.content),
        )
        self.assertNotIn("nobody@example.com", str(response.content))

    def test_linked_column_on_standalone_view_does_not_500(self):
        # TYPO: get_object_url called self.has_view_perm(...), which
        # doesn't exist (the real method is has_view_permission). Any
        # standalone ListModelView (no viewset) whose model defines
        # get_absolute_url crashed with AttributeError instead of
        # rendering the object link.
        with mock.patch.object(
            User, "get_absolute_url", lambda self: f"/users/{self.pk}/", create=True
        ):
            response = self.client.get("/linked_user/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(f'href="/users/{self.admin.pk}/"', str(response.content))

    def test_object_link_columns_default_does_not_substring_match(self):
        # get_object_link_columns() returned the first column *name as a
        # bare string* when object_link_columns was unset, so
        # `column.attr_name in self.get_object_link_columns` did substring
        # matching ("name" in "username" -> True) instead of an equality
        # check, wrongly linking a column whose name happens to be a
        # substring of the first column's name.
        with mock.patch.object(
            User, "get_absolute_url", lambda self: f"/users/{self.pk}/", create=True
        ):
            response = self.client.get("/linked_substring_user/")

        self.assertEqual(response.status_code, 200)
        content = str(response.content)

        href = f'href="/users/{self.admin.pk}/"'
        self.assertEqual(content.count(href), 1)

    def test_get_object_link_columns_does_not_leak_view_instances(self):
        # get_object_link_columns was @lru_cache(maxsize=None) on the
        # instance method, so `self` was part of the cache key -- every
        # view instance (created fresh per request) was pinned in that
        # never-evicted global cache forever, along with its request and
        # queryset.
        refs = []
        for _ in range(5):
            view = BaseListModelView()
            view.get_object_link_columns
            refs.append(weakref.ref(view))
            del view

        gc.collect()
        alive = sum(1 for r in refs if r() is not None)
        self.assertEqual(alive, 0)


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


class LinkedSubstringUserListView(ListModelView):
    # "name" is a substring of "username", the first (and only intended
    # link) column.
    model = User
    columns = ("username", "name")
    ordering = "pk"

    def name(self, obj):
        return obj.get_full_name() or obj.username


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
    path(
        "searchable_user/",
        ListModelView.as_view(
            model=User,
            columns=("first_name", "last_name", "email", "is_staff"),
            search_fields=("username",),
            ordering="pk",
        ),
    ),
    path(
        "linked_user/",
        ListModelView.as_view(
            model=User,
            columns=("username",),
            ordering="pk",
        ),
    ),
    path("linked_substring_user/", LinkedSubstringUserListView.as_view()),
]
