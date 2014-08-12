from django.conf.urls import patterns, include, url
from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.test import TestCase

from viewflow.site.base import ViewSite
from ...flows import SingleTaskFlow, AllTaskFlow


testsite = ViewSite(app_name='viewflow_test')
testsite.register(SingleTaskFlow)
testsite.register(AllTaskFlow)


urlpatterns = patterns('',  # NOQA
    url(r'^', include(testsite.urls)))


class TestURLReverse(TestCase):
    urls = 'tests.unit.tests.viewsite.test_urls'

    def test_django_reverse_flow_urls_succeed(self):
        index_url = reverse('viewflow:index', current_app=SingleTaskFlow._meta.namespace)
        self.assertEqual(index_url, '/singletask/')

        index_url = reverse('viewflow:index', current_app=AllTaskFlow._meta.namespace)
        self.assertEqual(index_url, '/alltask/')


class TestFlowUrlTag(TestCase):
    urls = 'tests.unit.tests.viewsite.test_urls'

    def test_index_resolve_succeed(self):
        template = Template("{% load viewflow %}{% flowurl 'unit/SingleTaskFlow' 'viewflow:index' %}")
        self.assertEqual(template.render(Context({})), '/singletask/')

