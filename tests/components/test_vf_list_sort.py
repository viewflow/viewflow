import time

from django.test import override_settings
from django.urls import path
from django.views.generic import TemplateView

from . import LiveTestCase


class TestPageView(TemplateView):
    template_name = "tests/vf_list_sort.html"


urlpatterns = [path("page/", TestPageView.as_view())]


@override_settings(ROOT_URLCONF=__name__)
class Test(LiveTestCase):
    def test_disconnect_removes_the_click_listener(self):
        # disconnectedCallback did
        # this._headEl.removeEventListener('click', this.onClick) --
        # this.onClick doesn't exist (the real handler is onHeadClick,
        # added in connectedCallback), so removeEventListener('click',
        # undefined) never actually removed the real listener.
        page_url = f"{self.live_server_url}/page/"
        self.browser.get(page_url)
        time.sleep(0.2)  # let connectedCallback's setTimeout wire up thead

        removed = self.browser.execute_script(
            """
            const head = document.querySelector('#the-list thead');
            const removed = [];
            const original = head.removeEventListener.bind(head);
            head.removeEventListener = (type, handler, ...args) => {
                removed.push([type, handler === undefined]);
                return original(type, handler, ...args);
            };
            document.getElementById('the-list').remove();
            return removed;
            """
        )

        # ['click', handler_is_undefined]
        click_removal = next(r for r in removed if r[0] == "click")
        self.assertFalse(
            click_removal[1], "click listener removed with an undefined handler"
        )
        self.assertNoJsErrors()

    def test_disconnect_before_connect_timeout_fires_does_not_throw(self):
        # If the element was removed from the DOM before
        # connectedCallback's setTimeout callback fired, this._headEl
        # was still undefined, and
        # this._headEl.removeEventListener(...) threw a TypeError.
        page_url = f"{self.live_server_url}/page/"
        self.browser.get(page_url)
        time.sleep(0.2)  # let the statically-present list finish mounting

        self.browser.execute_script(
            """
            const el = document.createElement('vf-list');
            el.dataset.listSortOrderParam = 'orderby';
            el.dataset.listSortPageParam = 'page';
            el.innerHTML = '<table><thead><tr><th></th></tr></thead></table>';
            document.body.appendChild(el);
            el.remove();
            """
        )
        time.sleep(0.2)

        self.assertNoJsErrors()
