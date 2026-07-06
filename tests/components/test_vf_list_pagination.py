from django.test import override_settings
from django.urls import path
from django.views.generic import TemplateView

from . import LiveTestCase


class TestPageView(TemplateView):
    template_name = "tests/vf_list_pagination.html"


urlpatterns = [path("page/", TestPageView.as_view())]


@override_settings(ROOT_URLCONF=__name__)
class Test(LiveTestCase):
    def test_disconnect_removes_the_document_level_turbo_listeners(self):
        # onClick's document-level turbo:load/turbo:before-render
        # listeners were only ever removed inside onTurboLoad -- a
        # failed visit never fires turbo:load, so the element getting
        # disconnected while a visit is still pending leaked them on
        # document forever.
        page_url = f"{self.live_server_url}/page/"
        self.browser.get(page_url)

        removed = self.browser.execute_script(
            """
            const pagination = document.getElementById('the-pagination');
            const removed = [];
            const original = document.removeEventListener.bind(document);
            document.removeEventListener = (type, handler, ...args) => {
                if (type === 'turbo:load' || type === 'turbo:before-render') {
                    removed.push(type);
                }
                return original(type, handler, ...args);
            };

            // Simulate the listener setup onClick performs, without
            // triggering a real Turbo visit.
            document.addEventListener('turbo:load', pagination.onTurboLoad);
            document.addEventListener('turbo:before-render', pagination.onBeforeRender);

            pagination.remove();

            return removed.sort();
            """
        )

        self.assertEqual(removed, ["turbo:before-render", "turbo:load"])
        self.assertNoJsErrors()

    def test_before_render_does_not_throw_without_a_vf_list_in_the_new_body(self):
        # onBeforeRender called
        # event.detail.newBody.querySelector('vf-list').classList.add(...)
        # with no null-check -- navigating to a page without a vf-list
        # threw a TypeError.
        page_url = f"{self.live_server_url}/page/"
        self.browser.get(page_url)

        self.browser.execute_script(
            """
            const pagination = document.getElementById('the-pagination');
            const newBody = document.createElement('body');
            pagination.onBeforeRender({detail: {newBody}});
            """
        )

        self.assertNoJsErrors()
