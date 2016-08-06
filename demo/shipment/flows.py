from viewflow import flow
from viewflow.base import this, Flow
from viewflow.flow.views import UpdateProcessView
from viewflow.lock import select_for_update_lock

from . import views
from .models import ShipmentProcess, ShipmentTask


class ShipmentFlow(Flow):
    process_class = ShipmentProcess
    task_class = ShipmentTask
    lock_impl = select_for_update_lock

    summary_template = """
        Shipment {{ process.shipment.shipmentitem_set.count }} items
        to {{ process.shipment.first_name }} {{ process.shipment.last_name }} / {{ process.shipment.city }}
        """

    start = (
        flow.Start(views.start_view)
        .Permission('shipment.can_start_request')
        .Next(this.split_clerk_warehouse)
    )

    # clerk
    split_clerk_warehouse = (
        flow.Split()
        .Next(this.shipment_type)
        .Next(this.package_goods)
    )

    shipment_type = (
        flow.View(
            views.ShipmentView, fields=["carrier"],
            task_description="Carrier selection")
        .Assign(lambda act: act.process.created_by)
        .Next(this.delivery_mode)
    )

    delivery_mode = (
        flow.If(cond=lambda act: act.process.is_normal_post())
        .Then(this.check_insurance)
        .Else(this.request_quotes)
    )

    request_quotes = (
        flow.View(
            views.ShipmentView,
            fields=["carrier_quote"])
        .Assign(lambda act: act.process.created_by)
        .Next(this.join_clerk_warehouse)
    )

    check_insurance = (
        flow.View(
            views.ShipmentView,
            fields=["need_insurance"])
        .Assign(lambda act: act.process.created_by)
        .Next('split_on_insurance')
    )

    split_on_insurance = (
        flow.Split()
        .Next(
            this.take_extra_insurance,
            cond=lambda act: act.process.need_extra_insurance())
        .Always(this.fill_post_label)
    )

    fill_post_label = (
        flow.View(
            views.ShipmentView,
            fields=["post_label"])
        .Assign(lambda act: act.process.created_by)
        .Next(this.join_on_insurance)
    )

    join_on_insurance = (
        flow.Join()
        .Next(this.join_clerk_warehouse)
    )

    # Logistic manager
    take_extra_insurance = (
        flow.View(views.InsuranceView)
        .Permission('shipment.can_take_extra_insurance')
        .Next(this.join_on_insurance)
    )

    # Warehouse worker
    package_goods = (
        flow.View(UpdateProcessView)
        .Permission('shipment.can_package_goods')
        .Next(this.join_clerk_warehouse)
    )

    join_clerk_warehouse = (
        flow.Join()
        .Next(this.move_package)
    )

    move_package = (
        flow.View(UpdateProcessView)
        .Assign(this.package_goods.owner)
        .Next(this.end)
    )

    end = flow.End()
