import re

from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Cast
from django.test import TestCase, override_settings
from django.urls import path
from viewflow import jsonstore
from viewflow.views import ListModelView


class JsonThing(models.Model):
    name = models.CharField(max_length=50)
    data = models.JSONField(default=dict)


class Invoice(models.Model):
    """A workflow-style model whose typed fields live in a JSONField.

    ``jsonstore`` fields (as used by custom flow ``Process`` models) route
    ``order_by("field")`` through the JSON key transform, so they are
    sortable by their plain name without an ``orderby_column``.
    """

    data = models.JSONField(default=dict)
    number = jsonstore.CharField(max_length=50)
    amount = jsonstore.IntegerField()


class InvoiceView(ListModelView):
    model = Invoice
    columns = ("number", "amount")
    ordering = "pk"


class StringOrderView(ListModelView):
    """A virtual column made sortable with a plain JSONField key lookup."""

    model = JsonThing
    columns = ("name", "price")
    ordering = "pk"

    def price(self, obj):
        return obj.data.get("price")

    price.orderby_column = "data__price"


class ExprOrderView(ListModelView):
    """A virtual column made sortable with a query expression.

    ``Cast`` forces a numeric sort so 2 < 10 instead of the lexical
    "10" < "2" a raw key transform would give.
    """

    model = JsonThing
    columns = ("name", "price")
    ordering = "pk"

    def price(self, obj):
        return obj.data.get("price")

    price.orderby_column = Cast("data__price", models.IntegerField())


urlpatterns = [
    path("str/", StringOrderView.as_view()),
    path("expr/", ExprOrderView.as_view()),
    path("invoice/", InvoiceView.as_view()),
]


@override_settings(ROOT_URLCONF=__name__)
class Test(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("a", "a@a.com", "a")
        self.assertTrue(self.client.login(username="a", password="a"))
        JsonThing.objects.create(name="c", data={"price": 30})
        JsonThing.objects.create(name="a", data={"price": 2})
        JsonThing.objects.create(name="b", data={"price": 10})

    def _row_order(self, response):
        return re.findall(r'table-cell-text">([abc])</td>', response.content.decode())

    def test_string_orderby_sorts_by_json_key(self):
        # A virtual column with orderby_column = "data__key" is clickable,
        # orders the queryset by the JSON key, and renders the sort arrow.
        response = self.client.get("/str/?_orderby=price")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertIn('data-list-sort-column="price"', content)
        self.assertIn("vf-list__table-header--sort-asc", content)

    def test_expr_orderby_sorts_numerically(self):
        # orderby_column may be a query expression (Cast, KeyTextTransform,
        # ...). Cast to int makes 2 sort before 10 (a raw text sort would
        # put "10" first).
        response = self.client.get("/expr/?_orderby=price")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._row_order(response), ["a", "b", "c"])  # 2, 10, 30
        self.assertIn('data-list-sort-column="price"', content)
        # expression-ordered columns now render the sort indicator too
        self.assertIn("vf-list__table-header--sort-asc", content)

    def test_expr_orderby_descending(self):
        response = self.client.get("/expr/?_orderby=-price")
        content = response.content.decode()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._row_order(response), ["c", "b", "a"])  # 30, 10, 2
        self.assertIn("vf-list__table-header--sort-desc", content)

    def test_jsonstore_field_column_sorts_numerically(self):
        # A workflow-style model with typed jsonstore fields: the column is
        # the field itself, sortable by plain name with no orderby_column,
        # and jsonstore extracts the typed value so 2 sorts before 10.
        Invoice.objects.create(number="c", amount=30)
        Invoice.objects.create(number="a", amount=2)
        Invoice.objects.create(number="b", amount=10)

        response = self.client.get("/invoice/?_orderby=amount")
        content = response.content.decode()
        order = re.findall(r'table-cell-text">([abc])</td>', content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(order, ["a", "b", "c"])  # 2, 10, 30
        self.assertIn('data-list-sort-column="amount"', content)
        self.assertIn("vf-list__table-header--sort-asc", content)
