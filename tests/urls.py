import django
from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView
from viewflow import site
from tests.unit.views import TestFormView


if django.VERSION < (1, 7):
    admin.autodiscover()
    site.autodiscover()


urlpatterns = patterns('',  # NOQA
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^flows/', include(site.viewsite.urls)),
    url(r'^viewflow/$', TemplateView.as_view(template_name='viewflow/process_index.html')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^examples/form/$', TestFormView.as_view()),
    url(r'^', include('tests.examples.website')),
)
