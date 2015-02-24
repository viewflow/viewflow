def create_items_flow(activation, order_item, parent_task=None):
    activation.prepare()

    activation.process.parent_task = parent_task
    activation.process.item = order_item
    activation.done()

    return activation
