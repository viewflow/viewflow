import time

from django.test import override_settings
from django.urls import path
from django.views.generic import TemplateView

from . import LiveTestCase


class TestPageView(TemplateView):
    template_name = "tests/vf_list_filter.html"


urlpatterns = [path("page/", TestPageView.as_view())]


@override_settings(ROOT_URLCONF=__name__)
class Test(LiveTestCase):
    def test_disconnect_destroys_the_actual_mdc_drawer_instance(self):
        # disconnectedCallback destroyed this._mdcTemporalDrawer and
        # this._mdcPersistentDrawer, but neither property is ever
        # assigned anywhere in the class -- the real drawer instance
        # lives in this._mdcDrawer. Removing the element from the DOM
        # (e.g. a Turbo navigation replacing the body) never actually
        # called .destroy() on it, leaking the MDC drawer's listeners.
        page_url = f"{self.live_server_url}/page/"
        self.browser.get(page_url)
        time.sleep(0.2)  # let connectedCallback's setTimeout mount the drawer

        self.browser.execute_script(
            """
            const el = document.getElementById('id_filter_drawer');
            window.__destroyCalled = false;
            el._mdcDrawer.destroy = () => { window.__destroyCalled = true; };
            el.remove();
            """
        )

        self.assertTrue(self.browser.execute_script("return window.__destroyCalled"))
        self.assertNoJsErrors()
