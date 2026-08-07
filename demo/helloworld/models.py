from viewflow import jsonstore
from viewflow.workflow.models import Process


class PizzaOrder(Process):
    customer_name = jsonstore.CharField(max_length=250)
    address = jsonstore.TextField()
    toppings = jsonstore.TextField()
    tips_received = jsonstore.IntegerField(default=0)
    baking_time = jsonstore.IntegerField(default=10)

    class Meta:
        proxy = True
