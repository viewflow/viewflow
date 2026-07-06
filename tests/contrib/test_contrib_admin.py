from django.contrib.auth.models import User
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

    def test_has_view_permission_gates_by_is_staff(self):
        # has_perm(self, user) was dead code -- no base class or the
        # framework's dispatch/menu-rendering machinery calls that method
        # name (the expected one is has_view_permission), so the intended
        # is_staff gate was never actually applied and the "Administration"
        # menu entry showed to any authenticated user, not just staff.
        staff_user = User.objects.create_user(
            "staffer", password="pwd", is_staff=True
        )
        non_staff_user = User.objects.create_user(
            "nonstaffer", password="pwd", is_staff=False
        )

        admin_viewset = Admin()

        self.assertTrue(admin_viewset.has_view_permission(staff_user))
        self.assertFalse(admin_viewset.has_view_permission(non_staff_user))


urlpatterns = [
    path('', Site(viewsets=[Admin()]).urls)
]
