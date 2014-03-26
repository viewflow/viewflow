from django.conf.urls import patterns, url, include
from examples.onetwothree.flows.v1 import HelloWorldFlow

urlpatterns = patterns('',  # NOQA
    url(r'^flow/', include(HelloWorldFlow.instance.urls)))
