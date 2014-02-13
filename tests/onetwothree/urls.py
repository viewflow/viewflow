from django.conf.urls import patterns, url
from onetwothee.flows.v1 import StepFlow


urlpatterns = patterns('onetwothee.views',
    url(r'onetwothree/start/$', 'one', {'flow_task': StepFlow.start}),  # NOQA
)
