from selenium.webdriver.common.by import By
from django.test import override_settings
from django.urls import path
from django.views.generic import TemplateView
from viewflow.contrib.auth import AuthViewset
from viewflow.urls import Application, AppMenuMixin, IndexViewMixin, Site, Viewset

from . import LiveTestCase


@override_settings(ROOT_URLCONF=__name__, DEBUG=True)
class Test(LiveTestCase):
    fixtures = ["users.json"]

    def setUp(self):
        self.client.login(username="admin", password="admin")
        cookie = self.client.cookies["sessionid"]
        self.browser.get(self.live_server_url)
        self.browser.add_cookie(
            {"name": "sessionid", "value": cookie.value, "secure": False, "path": "/"}
        )
        self.browser.refresh()

    def test_page_navigation(self):
        self.browser.get(f"{self.live_server_url}/application/test/test/")
        self.assertNoJsErrors()

        app_nav_link = self.browser.find_element(
            By.XPATH, '//aside//a[@href="/application/test/"]'
        )
        self.assertIn(
            "mdc-list-item--selected", app_nav_link.get_attribute("class").split(" ")
        )

        site_nav_link = self.browser.find_element(
            By.XPATH, '//aside//a[@href="/application/"]'
        )
        self.assertIn(
            "mdc-list-item--selected", site_nav_link.get_attribute("class").split(" ")
        )

        # navigation click
        site_nav_link = self.browser.find_element(
            By.XPATH, '//aside//a[@href="/application2/"]'
        )
        site_nav_link.click()

        site_nav_link = self.browser.find_element(
            By.XPATH, '//aside//a[@href="/application2/"]'
        )
        self.assertIn(
            "mdc-list-item--selected", site_nav_link.get_attribute("class").split(" ")
        )

        self.assertNoJsErrors()

    def test_drawer_resize(self):
        self.browser.set_window_size(1280, 947)
        self.browser.get(f"{self.live_server_url}/application/test/")

        drawer = self.browser.find_element(By.CSS_SELECTOR, ".vf-page__menu")
        drawer_classes = drawer.get_attribute("class").split(" ")
        self.assertIn("mdc-drawer--dismissible", drawer_classes)
        self.assertIn("mdc-drawer--open", drawer_classes)
        self.assertNotIn("mdc-drawer--modal", drawer_classes)

        self.browser.set_window_size(640, 480)
        self.browser.execute_script("return;")  # allow js resize hooks to e executed
        drawer_classes = drawer.get_attribute("class").split(" ")
        self.assertNotIn("mdc-drawer--dismissible", drawer_classes)
        self.assertNotIn("mdc-drawer--open", drawer_classes)
        self.assertIn("mdc-drawer--modal", drawer_classes)

        self.browser.set_window_size(1280, 947)
        self.browser.execute_script("return;")  # allow js resize hooks to e executed
        drawer_classes = drawer.get_attribute("class").split(" ")
        self.assertIn("mdc-drawer--dismissible", drawer_classes)
        self.assertIn("mdc-drawer--open", drawer_classes)
        self.assertNotIn("mdc-drawer--modal", drawer_classes)

        self.assertNoJsErrors()

    def test_header_menu(self):
        self.assertTrue(self.login(username="admin", password="admin"))
        self.browser.get(f"{self.live_server_url}/application/test/")

        primary_menu = self.browser.find_element(
            By.CSS_SELECTOR, ".vf-page__menu-primary"
        )
        secondary_menu = self.browser.find_element(
            By.CSS_SELECTOR, ".vf-page__menu-secondary"
        )
        button = self.browser.find_element(
            By.CSS_SELECTOR, ".vf-page__menu-toggle-button"
        )

        self.assertTrue(primary_menu.is_displayed())
        self.assertFalse(secondary_menu.is_displayed())
        button.click()
        self.assertFalse(primary_menu.is_displayed())
        self.assertTrue(secondary_menu.is_displayed())

        self.assertNoJsErrors()


class TestViewset(IndexViewMixin, AppMenuMixin, Viewset):
    title = "Test Viewset"
    page_path = path(
        "test/",
        TemplateView.as_view(template_name="viewflow/base_page.html"),
        name="page",
    )


urlpatterns = [
    path(
        "",
        Site(
            viewsets=[
                Application(title="Test Application", viewsets=[TestViewset()]),
                Application(
                    app_name="application2",
                    title="Test Application 2",
                    viewsets=[TestViewset()],
                ),
            ]
        ).urls,
    ),
    path("accounts/", AuthViewset().urls),
]
