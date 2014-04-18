from django.conf.urls import patterns, url, include
from examples.helloworld.flows import HelloWorldFlow

urlpatterns = patterns('',  # NOQA
    url(r'^', include(HelloWorldFlow.instance.urls)))
