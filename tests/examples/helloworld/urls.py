from django.conf.urls import patterns, url, include
from .flows import HelloWorldFlow

urlpatterns = patterns('',  # NOQA
    url(r'^', include(HelloWorldFlow.instance.urls)))
