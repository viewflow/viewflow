from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView
from unit.views import TestFormView


admin.autodiscover()


urlpatterns = patterns('',  # NOQA
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^viewflow/$', TemplateView.as_view(template_name='viewflow/process_index.html')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^examples/shipment/', include('tests.examples.shipment.urls')),
    url(r'^examples/helloworld/', include('tests.examples.helloworld.urls')),
    url(r'^examples/form/$', TestFormView.as_view()),
    url(r'^', include('examples.website')),
)
