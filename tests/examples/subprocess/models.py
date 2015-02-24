from django.db import models
from viewflow.models import Process


class Order(models.Model):
    name = models.CharField(max_length=150)
    address = models.TextField()


class OrderItem(models.Model):
    order = models.ForeignKey(Order)
    title = models.CharField(max_length=150)
    quantity = models.IntegerField(default=1)


class OrderProcess(Process):
    order = models.ForeignKey(Order)


class OrderItemProcess(Process):
    parent_task = models.ForeignKey(OrderProcess.task_cls, blank=True, null=True)
    item = models.ForeignKey(OrderItem)
