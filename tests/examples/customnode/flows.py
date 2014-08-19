from viewflow import flow
from viewflow.base import this, Flow
from viewflow.site import viewsite
from viewflow.views import StartView

from . import models, views
from .nodes import DynamicSplit


class DynamicSplitFlow(Flow):
    """
    Dynamic split

    Depends on initial decision, several instances on make_decision task would be instanciated
    """
    process_cls = models.DynamicSplitProcess

    start = flow.Start(StartView, fields=['split_count']) \
        .Permission(auto_create=True) \
        .Next(this.spit_on_decision)

    spit_on_decision = DynamicSplit(lambda p: p.split_count) \
        .Next(this.make_decision)

    make_decision = flow.View(views.DecisionView) \
        .Next(this.join_on_decision)

    join_on_decision = flow.Join() \
        .Next(this.end)

    end = flow.End()


viewsite.register(DynamicSplitFlow)
