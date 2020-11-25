import shutil

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from selenium import webdriver


@tag('selenium')
class LiveTestCase(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.assertTrue(shutil.which('geckodriver'), "`geckodriver` not found")

        cls.browser = webdriver.Firefox()
        cls.browser.implicitly_wait(10)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def login(self, **credentials):
        self.browser.get(self.live_server_url)
        logged_in = self.client.login(**credentials)
        if logged_in:
            auth_cookie = {
                **self.client.cookies[settings.SESSION_COOKIE_NAME],
                'name': settings.SESSION_COOKIE_NAME,
                'value': self.client.session.session_key,
                'secure': settings.SESSION_COOKIE_SECURE or False,
            }
            self.browser.add_cookie(auth_cookie)

        return logged_in

    def assertNoJsErrors(self):
        errors = self.browser.execute_script('return window.errors')
        self.browser.execute_script('window.errors=[]')
        self.assertFalse(errors)
