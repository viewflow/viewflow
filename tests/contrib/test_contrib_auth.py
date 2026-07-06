import html5lib
from io import BytesIO
from PIL import Image
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.test import TestCase, RequestFactory, tag, override_settings
from django.urls import path
from viewflow.contrib import auth


def _png_bytes(size=(10, 10)):
    buf = BytesIO()
    Image.new("RGB", size, color="red").save(buf, format="PNG")
    buf.seek(0)
    return buf


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@admin.com", "admin")
        self.user = User.objects.create_user("user", "user@user.com", "user")
        self.validator = html5lib.HTMLParser(strict=True)

    @tag("integration")
    def test_change_user_avatar(self):
        img = _png_bytes()
        img.name = "avatar.png"

        request = RequestFactory().post("/", {"avatar": img})
        request.user = self.admin

        view = auth.ProfileView()
        view.setup(request)
        try:
            response = view.post(request)
            self.assertEqual(response.status_code, 200)
            self.assertIn("/media/avatars/", auth.get_user_avatar_url(self.admin))
        finally:
            default_storage.delete("avatars/{}.png".format(self.admin.pk))

    @tag("integration")
    def test_avatar_upload_rejects_non_image_content(self):
        # AvatarForm used forms.FileField (not ImageField), so it never
        # validated the upload is actually an image, and
        # default_storage.save's max_length kwarg limits the *filename*
        # length, not the file's byte size -- so arbitrary non-image
        # content of any size could be stored as avatars/<pk>.png.
        fake_avatar = BytesIO(b"not actually an image, just some bytes")
        fake_avatar.name = "avatar.png"

        request = RequestFactory().post("/", {"avatar": fake_avatar})
        request.user = self.user

        view = auth.ProfileView()
        view.setup(request)
        file_name = "avatars/{}.png".format(self.user.pk)
        try:
            response = view.post(request)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(default_storage.exists(file_name))
        finally:
            if default_storage.exists(file_name):
                default_storage.delete(file_name)

    @tag("integration")
    def test_avatar_upload_rejects_oversized_image(self):
        # Regression guard for the size-limit half of the fix: even a
        # genuinely valid image is rejected once it exceeds the cap.
        oversized = BytesIO()
        Image.new("RGB", (2000, 2000)).save(oversized, format="BMP")
        oversized.seek(0)
        oversized.name = "avatar.png"

        request = RequestFactory().post("/", {"avatar": oversized})
        request.user = self.user

        view = auth.ProfileView()
        view.setup(request)
        file_name = "avatars/{}.png".format(self.user.pk)
        try:
            response = view.post(request)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(default_storage.exists(file_name))
        finally:
            if default_storage.exists(file_name):
                default_storage.delete(file_name)

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
