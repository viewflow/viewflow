from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from unit.forms import AllElementsForm


admin.autodiscover()


urlpatterns = patterns('',  # NOQA
    url(r'^$', TemplateView.as_view(template_name='index.html')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^examples/shipment/', include('examples.shipment.urls')),
    url(r'^examples/helloworld/', include('examples.helloworld.urls')),
    url(r'^examples/form/$', FormView.as_view(
        form_class=AllElementsForm,
        template_name='unit/form.html')),
    url(r'^', include('examples.website')),
)
