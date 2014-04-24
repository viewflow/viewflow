from viewflow import flow
from viewflow.base import this, Flow
from viewflow.views import TaskView
from viewflow.lock import select_for_update_lock

from examples.shipment import views
from examples.shipment.models import ShipmentProcess


class ShipmentFlow(Flow):
    process_cls = ShipmentProcess
    lock_impl = select_for_update_lock

    start = flow.Start(views.StartView) \
        .Activate(this.split_clerk_warehouse) \
        .Permission('shipment.can_start_request')

    # clerk
    split_clerk_warehouse = flow.Split() \
        .Next(this.shipment_type) \
        .Next(this.package_goods)

    shipment_type = flow.View(views.ShipmentView, fields=["carrier"]) \
        .Next(this.delivery_mode) \
        .Assign(lambda p: p.created_by)

    delivery_mode = flow.If(cond=lambda a: a.process.is_normal_post()) \
        .OnTrue(this.check_insurance) \
        .OnFalse(this.request_quotes)

    request_quotes = flow.View(views.ShipmentView, fields=["carrier_quote"]) \
        .Next(this.join_delivery_mode) \
        .Assign(lambda p: p.created_by)

    check_insurance = flow.View(TaskView.as_view()) \
        .Next('split_on_insurance') \
        .Assign(lambda p: p.created_by)

    split_on_insurance = flow.Split() \
        .Next(this.take_extra_insurance, cond=lambda a: a.process.need_extra_insurance()) \
        .Always(this.fill_post_label)

    fill_post_label = flow.View(TaskView.as_view()) \
        .Next(this.join_on_insurance) \
        .Assign(lambda a: a.process.shipmentprocess.created_by)

    join_on_insurance = flow.Join() \
        .Next(this.join_delivery_mode)

    join_delivery_mode = flow.Join(wait_all=False) \
        .Next(this.join_clerk_warehouse)

    # Logistic manager
    take_extra_insurance = flow.View(TaskView.as_view()) \
        .Next(this.join_on_insurance) \
        .Permission('shipment.can_take_extra_insurance')

    # Warehouse worker
    package_goods = flow.View(TaskView.as_view()) \
        .Next(this.join_clerk_warehouse) \
        .Permission('shipment.can_package_goods')

    join_clerk_warehouse = flow.Join() \
        .Next(this.move_package)

    move_package = flow.View(TaskView.as_view()) \
        .Next(this.end) \
        .Permission('shipment.can_move_package')

    end = flow.End()
