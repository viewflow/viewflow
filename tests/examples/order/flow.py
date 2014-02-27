from viewflow import flow
from order import views


class CustomerOrderFlow(flow.Flow):
    order_received = flow.Start() \
        .Activate(views.check_availability)

    check_availability = flow.View(views.check_availability) \
        .Next('is_article_available')

    is_article_available = flow.If(condition=lambda process: process.article_available()) \
        .OnTrue(views.ship_article) \
        .OnFalse('procurement')

    procurement = flow.Subprocess('order.flow.ProcurementFlow') \
        .OnExcalation(views.inform_customer) \
        .OnError(views.error_inform_customer) \
        .Next(views.ship_article)

    ship_article = flow.View(views.ship_article) \
        .Next(views.financial_settlement)

    financial_settlement = flow.View(views.financial_settlement) \
        .Next('payment_received')

    payment_received = flow.End()

    inform_customer = flow.View(views.inform_customer) \
        .Next('customent_informed')

    customent_informed = flow.EndPath()

    error_inform_customer = flow.View(views.error_inform_customer) \
        .Next(views.clean_catalogue)

    clean_catalogue = flow.View(views.clean_catalogue) \
        .Next('article_removed')

    article_removed = flow.End()


class LowStockFlow(flow.Flow):
    low_stock = flow.Start() \
        .Activate('procurement')

    procurement = flow.Subprocess('order.flow.ProcurementFlow') \
        .OnError(views.clean_catalogue) \
        .Next('article_procured')

    clean_catalogue = flow.View(views.clean_catalogue) \
        .Next('article_removed')

    article_procured = flow.End()

    article_removed = flow.End()


class ProcurementFlow(flow.Flow):
    start = flow.Start()

    check_availability = flow.Views(views.check_supplier_availability) \
        .Next('is_deliverable')

    is_deliverable = flow.Switch() \
        .Case(views.order, cond=lambda process: process.fast_delivarable()) \
        .Case('late_delivery', cond=lambda process: process.late_delivarable()) \
        .Default('undelivarable')

    order = flow.View(views.order) \
        .Next('article_received')

    article_received = flow.MailBox() \
        .Next('article_procured')

    article_procured = flow.End()

    late_delivarable = flow.EscalationEvent() \
        .Next(views.order)

    undelivarable = flow.Error()
