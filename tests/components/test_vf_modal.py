from django.test import override_settings
from django.urls import path
from django.views.generic import TemplateView

from . import LiveTestCase


class TestPageView(TemplateView):
    template_name = "tests/vf_modal_trigger.html"


urlpatterns = [path("page/", TestPageView.as_view())]


@override_settings(ROOT_URLCONF=__name__)
class Test(LiveTestCase):
    def test_disconnect_removes_the_button_click_listener_added(self):
        # disconnectedCallback removed this._buttonEl's 'click' listener
        # with this.onOpenDialog, but the handler actually added in
        # connectedCallback was this.onCloseDialog -- a mismatched
        # reference means removeEventListener never matched anything,
        # leaking the real listener.
        page_url = f"{self.live_server_url}/page/"
        self.browser.get(page_url)

        result = self.browser.execute_script(
            """
            // Spy on addEventListener/removeEventListener on
            // HTMLElement.prototype so it also covers the dynamically
            // created button element, capturing the exact handler
            // reference used for the button's 'click' listener at add
            // time and at remove time.
            const added = {};
            const removed = {};
            const originalAdd = HTMLElement.prototype.addEventListener;
            const originalRemove = HTMLElement.prototype.removeEventListener;
            HTMLElement.prototype.addEventListener = function(type, handler, ...args) {
                if (this.classList && this.classList.contains('vf-modal-trigger__button') && type === 'click') {
                    added.handler = handler;
                }
                return originalAdd.call(this, type, handler, ...args);
            };
            HTMLElement.prototype.removeEventListener = function(type, handler, ...args) {
                if (this.classList && this.classList.contains('vf-modal-trigger__button') && type === 'click') {
                    removed.handler = handler;
                }
                return originalRemove.call(this, type, handler, ...args);
            };

            const el = document.createElement('vf-modal-trigger');
            el.innerHTML = `
                <div class="vf-modal-trigger__content">content</div>
                <button class="vf-modal-trigger__button" type="button">Open</button>
            `;
            document.getElementById('host').appendChild(el);
            el.remove();

            HTMLElement.prototype.addEventListener = originalAdd;
            HTMLElement.prototype.removeEventListener = originalRemove;

            return {
                addedIsFunction: typeof added.handler === 'function',
                removedMatchesAdded: removed.handler === added.handler,
            };
            """
        )

        self.assertTrue(result["addedIsFunction"])
        self.assertTrue(
            result["removedMatchesAdded"],
            "removeEventListener was called with a different handler than "
            "the one addEventListener registered",
        )
        self.assertNoJsErrors()
