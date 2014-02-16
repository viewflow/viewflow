from django.conf.urls import patterns, url
from onetwothree.flows.v1 import StepFlow


urlpatterns = patterns('onetwothree.views',  # NOQA
    url(r'onetwothree/list/$', 'list',
        {'flow_cls': StepFlow}, name='flow'),
    url(r'onetwothree/start/$', 'start',
        {'start_task': StepFlow.start}, name='start'),
    url(r'onetwothree/one/$', 'one',
        {'flow_task': StepFlow.one}),
    url(r'onetwothree/two/$', 'two',
        {'flow_task': StepFlow.two}),
    url(r'onetwothree/three/$', 'three',
        {'flow_task': StepFlow.three}),
    url(r'onetwothree/end/$', 'end',
        {'flow_task': StepFlow.end}),
)
