from django.conf.urls import patterns, include, url
from django.contrib import admin
import viewflow

admin.autodiscover()
viewflow.autodiscover()


urlpatterns = patterns('',
    url(r'^flow/', include(viewflow.site.urls)),
    url(r'^admin/', include(admin.site.urls)),
)

