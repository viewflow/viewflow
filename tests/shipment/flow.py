from viewflow import flow
from shipment import views


class Shipmentflow(flow.Flow):
    start = flow.Start() \
        .Activate('split_clerk_warehouse')

    # clerk
    split_clerk_warehouse = flow.Split() \
        .Next(views.shipment_type) \
        .Next(views.package_goods)

    shipment_type = flow.View(views.shipment_type) \
        .Next('delivery_mode')

    delivery_mode = flow.If(cond=lambda process: process.is_normal_post()) \
        .OnTrue(views.check_insurance) \
        .OnFalse(views.request_quotes)

    request_quotes = flow.View(views.request_quotes) \
        .Next(views.assign_carrier)

    assign_carrier = flow.View(views.assign_carrier) \
        .Next('join_delivery_mode')

    check_insurance = flow.View(views.check_insurance) \
        .Next('split_on_insurance')

    split_on_insurance = flow.Split() \
        .Next(views.take_extra_insurance, cond=lambda process: process.need_extra_insurance()) \
        .Always(views.fill_post_label)

    fill_post_label = flow.View(views.fill_post_label) \
        .Next('join_on_insurance')

    join_on_insurance = flow.Join() \
        .Next('join_delivery_mode')

    join_delivery_mode = flow.Join() \
        .Next('join_clerk_warehouse')

    # Logistic manager
    take_extra_insurance = flow.View(views.take_extra_insurance) \
        .Next('join_on_insurance')

    # Warehouse worker
    package_goods = flow.View(views.package_goods) \
        .Next('join_clerk_warehouse')

    join_clerk_warehouse = flow.Join() \
        .Next(views.move_package)

    move_package = flow.View(views.move_package) \
        .Next('end')

    end = flow.End()

