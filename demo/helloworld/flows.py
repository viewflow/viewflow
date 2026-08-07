from viewflow import this
from viewflow.workflow import flow
from viewflow.workflow.flow.views import CreateProcessView, UpdateProcessView

from .models import PizzaOrder


class PizzaFlow(flow.Flow):
    process_class = PizzaOrder

    start = flow.Start(
        CreateProcessView.as_view(
            fields=["customer_name", "address", "toppings"]
        )
    ).Next(this.bake)

    bake = flow.View(
        UpdateProcessView.as_view(fields=["baking_time"])
    ).Next(this.deliver)

    deliver = flow.View(
        UpdateProcessView.as_view(fields=["tips_received"])
    ).Next(this.end)

    end = flow.End()
