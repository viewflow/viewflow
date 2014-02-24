from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView
from viewflow import flowsite

admin.autodiscover()
flowsite.autodiscover()


urlpatterns = patterns('',  # NOQA
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^flow/', include(flowsite.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^samples/shipment', include('shipment.urls', namespace="shipment")),
    url(r'^samples/onetwothree/', include('onetwothree.urls', namespace="onetwothree"))
)
