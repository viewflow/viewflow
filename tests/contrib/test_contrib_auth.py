import html5lib
from io import BytesIO
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory, tag, override_settings
from django.urls import path
from viewflow.contrib import auth


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@admin.com", "admin")
        self.user = User.objects.create_user("user", "user@user.com", "user")
        self.validator = html5lib.HTMLParser(strict=True)

    @tag("integration")
    def test_change_user_avatar(self):
        img = BytesIO(b"my_binary_data")
        img.name = "avatar.png"

        request = RequestFactory().post("/", {"avatar": img})
        request.user = self.admin

        view = auth.ProfileView()
        view.setup(request)

        response = view.post(request)
        self.assertEquals(response.status_code, 200)
        self.assertIn("/media/avatars/", auth.get_user_avatar_url(self.admin))

    @tag("integration")
    def test_get_default_user_avatar_url(self):
        """If no user avatar exists, use the default media."""
        self.assertEqual(
            auth.get_user_avatar_url(self.user), "/static/viewflow/img/user.png"
        )

    def test_profile_page(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get("/accounts/profile/")
        self.assertEqual(response.status_code, 200)
        self.validator.parse(response.content)

    def test_login_page(self):
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        self.validator.parse(response.content)

    def _test_logout_page(self):
        response = self.client.get("/accounts/logout/")
        self.assertEqual(response.status_code, 200)
        self.validator.parse(response.content)

    def test_password_change(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get("/accounts/password_change/")
        self.assertEqual(response.status_code, 200)
        self.validator.parse(response.content)

    def test_password_change_done(self):
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get("/accounts/password_change/done/")
        self.assertEqual(response.status_code, 200)
        self.validator.parse(response.content)

    def test_password_reset_request(self):
        response = self.client.get("/accounts/password_reset/")
        self.assertEqual(response.status_code, 200)
        self.validator.parse(response.content)

    def test_password_reset_request_done(self):
        response = self.client.get("/accounts/password_reset/done/")
        self.assertEqual(response.status_code, 200)
        self.validator.parse(response.content)

    def _test_password_reset(self):
        pass  # TODO

    def test_password_reset_complete(self):
        response = self.client.get("/accounts/reset/done/")
        self.assertEqual(response.status_code, 200)
        self.validator.parse(response.content)


urlpatterns = [
    path("accounts/", auth.AuthViewset().urls),
]
