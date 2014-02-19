from django.conf.urls import patterns, url
from onetwothree.flows.v1 import StepFlow


urlpatterns = patterns('onetwothree.views',  # NOQA
    url(r'onetwothree/list/$', 'list',
        {'flow_cls': StepFlow}),
    url(r'onetwothree/start/$', 'start',
        {'start_task': StepFlow.start}, name='v1_stepflow__start'),
    url(r'onetwothree/one/$', 'one',
        {'flow_task': StepFlow.one}, name='v1_stepflow__one'),
    url(r'onetwothree/two/$', 'two',
        {'flow_task': StepFlow.two}, name='v1_stepflow__two'),
    url(r'onetwothree/three/$', 'three',
        {'flow_task': StepFlow.three}, name='v1_stepflow__three'),
    url(r'onetwothree/end/$', 'end',
        {'flow_task': StepFlow.end}, name='v1_stepflow__end'),
)
