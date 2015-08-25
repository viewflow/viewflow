from viewflow import flow, views as flow_views
from viewflow.base import this, Flow

from . import models, tasks
from .nodes import ItemsSubprocess


class OrderItemFlow(Flow):
    start = flow.StartFunction(tasks.create_items_flow).Next(this.prepare)
    prepare = flow.View().Next(this.end)
    end = flow.End()


class OrderFlow(Flow):
    process_cls = models.OrderProcess

    start = flow.Start(flow_views.StartProcessView, fields=['split_count']) \
                .Permission(auto_create=True) \
                .Next(this.process_items)

    process_items = ItemsSubprocess(OrderItemFlow.start, lambda p: p.order.orderitem_set.all())
