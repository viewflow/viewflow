from django.urls import include, re_path
from django.contrib.auth.models import User
from django.db import models
from django.test import TestCase, RequestFactory
from django.urls import resolve
from django.views import generic

from viewflow import flow
from viewflow.activation import STATUS
from viewflow.base import Flow, this
from viewflow.flow import views, viewset


class Test(TestCase):
    def test_startview_mixin_with_create_view(self):
        class StartView(views.StartFlowMixin, generic.CreateView):
            model = StartViewFlowEntity
            fields = []

        view = StartView.as_view()
        user = User.objects.create(username='test', is_superuser=True)

        # get
        request = RequestFactory().get('/start/')
        request.user = user
        request.resolver_match = resolve('/test/start/')
        response = view(request, flow_class=StartViewTestFlow, flow_task=StartViewTestFlow.start)

        self.assertEqual(response.template_name,
                         ('tests/test_views_start/startviewtest/start.html',
                          'tests/test_views_start/startviewtest/start.html',
                          'viewflow/flow/start.html'))

        # post
        request = RequestFactory().post('/start/')
        request.user = user
        request.resolver_match = resolve('/test/start/')
        response = view(request, flow_class=StartViewTestFlow, flow_task=StartViewTestFlow.start)
        self.assertEqual(response.status_code, 302)

        process = StartViewTestFlow.process_class.objects.all()[0]
        process.get_task(StartViewTestFlow.start, status=[STATUS.DONE])

    def test_startprocess_view(self):
        view = views.CreateProcessView.as_view()
        user = User.objects.create(username='test', is_superuser=True)

        # get
        request = RequestFactory().get('/start/')
        request.user = user
        request.resolver_match = resolve('/test/start/')
        response = view(request, flow_class=StartViewTestFlow, flow_task=StartViewTestFlow.start)

        self.assertEqual(response.template_name,
                         ('tests/test_views_start/startviewtest/start.html',
                          'tests/test_views_start/startviewtest/start.html',
                          'viewflow/flow/start.html'))

        # post
        request = RequestFactory().post('/start/')
        request.user = user
        request.resolver_match = resolve('/test/start/')
        response = view(request, flow_class=StartViewTestFlow, flow_task=StartViewTestFlow.start)
        self.assertEqual(response.status_code, 302)

        process = StartViewTestFlow.process_class.objects.all()[0]
        process.get_task(StartViewTestFlow.start, status=[STATUS.DONE])


class StartViewTestFlow(Flow):
    start = flow.Start().Next(this.end)
    end = flow.End()


class StartViewFlowEntity(models.Model):
    pass


urlpatterns = [
    re_path(r'^test/', include((viewset.FlowViewSet(StartViewTestFlow).urls, 'startviewtest')))
]

try:
    from django.test import override_settings
    Test = override_settings(ROOT_URLCONF=__name__)(Test)
except ImportError:
    """
    django 1.6
    """
    Test.urls = __name__
