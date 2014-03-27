from django.conf.urls import patterns, url, include
from examples.helloworld.flows import HelloWorldFlow

urlpatterns = patterns('',  # NOQA
    url(r'^flow/', include(HelloWorldFlow.instance.urls)))
