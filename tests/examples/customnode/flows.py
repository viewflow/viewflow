from viewflow import flow, views as flow_views
from viewflow.base import this, Flow

from . import models, views
from .nodes import DynamicSplit


class DynamicSplitFlow(Flow):
    """
    Dynamic split

    Depends on initial decision, several instances on make_decision task would be instanciated
    """
    process_cls = models.DynamicSplitProcess

    start = flow.Start(flow_views.StartProcessView, fields=['split_count']) \
        .Permission(auto_create=True) \
        .Next(this.spit_on_decision)

    spit_on_decision = DynamicSplit(lambda p: p.split_count) \
        .Next(this.make_decision)

    make_decision = flow.View(views.DecisionView) \
        .Next(this.join_on_decision)

    join_on_decision = flow.Join() \
        .Next(this.end)

    end = flow.End()
