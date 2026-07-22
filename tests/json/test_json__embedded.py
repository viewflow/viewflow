import uuid
from datetime import date

from django.db import connection, models
from django.test import TestCase
from viewflow import jsonstore


class Money(jsonstore.EmbeddedModel):
    amount = jsonstore.IntegerField()
    currency = jsonstore.CharField(max_length=3, default="USD")


class Meta(jsonstore.EmbeddedModel):
    created = jsonstore.DateField(null=True)
    token = jsonstore.UUIDField(null=True)
    kind = jsonstore.CharField(max_length=10, default="std")
    # a custom key inside the embedded document
    label = jsonstore.CharField(max_length=20, json_key="lbl", null=True)


class Line(jsonstore.EmbeddedModel):
    """An embedded model that itself embeds another (nested document)."""

    price = jsonstore.EmbeddedField(Money, null=True, blank=True)
    qty = jsonstore.IntegerField(default=1)


class Product(models.Model):
    data = models.JSONField(default=dict)
    extra = models.JSONField(default=dict)

    price = jsonstore.EmbeddedField(Money, null=True, blank=True)
    # placed at a nested path in the parent
    info = jsonstore.EmbeddedField(
        Meta, json_key=("meta", "info"), null=True, blank=True
    )
    # stored in a different column
    line = jsonstore.EmbeddedField(Line, json_field_name="extra", null=True, blank=True)


class ConstructionTest(TestCase):
    def test_stores_nested_document(self):
        product = Product(price=Money(amount=100, currency="USD"))

        self.assertEqual(product.data, {"price": {"amount": 100, "currency": "USD"}})

    def test_read_returns_embedded_instance(self):
        product = Product(price=Money(amount=100, currency="EUR"))

        self.assertIsInstance(product.price, Money)
        self.assertEqual(product.price.amount, 100)
        self.assertEqual(product.price.currency, "EUR")

    def test_missing_reads_none(self):
        self.assertIsNone(Product().price)

    def test_embedded_field_default_applies(self):
        product = Product(price=Money(amount=5))

        self.assertEqual(product.price.currency, "USD")

    def test_unknown_field_kwarg_raises(self):
        with self.assertRaises(TypeError):
            Money(amount=1, bogus=2)

    def test_assign_dict_is_accepted(self):
        product = Product(price={"amount": 7, "currency": "GBP"})

        self.assertEqual(product.price.amount, 7)

    def test_equality_by_document(self):
        product = Product(price=Money(amount=9, currency="USD"))

        self.assertEqual(product.price, Money(amount=9, currency="USD"))
        self.assertNotEqual(product.price, Money(amount=8, currency="USD"))


class WriteThroughTest(TestCase):
    def test_inplace_edit_is_reflected(self):
        product = Product(price=Money(amount=100, currency="USD"))

        product.price.amount = 120

        self.assertEqual(product.data["price"]["amount"], 120)
        self.assertEqual(product.price.amount, 120)

    def test_assigning_none_clears(self):
        product = Product(price=Money(amount=1))

        product.price = None

        self.assertIsNone(product.price)

    def test_assignment_is_copied_not_aliased(self):
        money = Money(amount=1, currency="USD")
        product = Product(price=money)

        money.amount = 999  # mutating the original must not leak into the row

        self.assertEqual(product.price.amount, 1)


class TypedAndNestedTest(TestCase):
    def test_typed_fields_serialize(self):
        token = uuid.uuid4()
        product = Product(info=Meta(created=date(2020, 1, 2), token=token))

        self.assertEqual(
            product.data["meta"]["info"],
            {"created": "2020-01-02", "token": str(token)},
        )

    def test_typed_fields_deserialize(self):
        token = uuid.uuid4()
        product = Product(info=Meta(created=date(2020, 1, 2), token=token))

        self.assertEqual(product.info.created, date(2020, 1, 2))
        self.assertIsInstance(product.info.created, date)
        self.assertEqual(product.info.token, token)
        self.assertIsInstance(product.info.token, uuid.UUID)

    def test_custom_key_inside_embedded(self):
        product = Product(info=Meta(label="hi"))

        self.assertEqual(product.data["meta"]["info"], {"lbl": "hi"})
        self.assertEqual(product.info.label, "hi")

    def test_custom_json_column(self):
        product = Product(line=Line(qty=3))

        self.assertEqual(product.extra, {"line": {"qty": 3}})
        self.assertEqual(product.data, {})

    def test_nested_embedded_document(self):
        product = Product(line=Line(qty=2, price=Money(amount=50, currency="EUR")))

        self.assertEqual(
            product.extra["line"],
            {"qty": 2, "price": {"amount": 50, "currency": "EUR"}},
        )
        self.assertEqual(product.line.price.amount, 50)

    def test_nested_embedded_write_through(self):
        product = Product(line=Line(qty=1, price=Money(amount=10)))

        product.line.price.amount = 99

        self.assertEqual(product.extra["line"]["price"]["amount"], 99)


class RoundtripTest(TestCase):
    def test_db_roundtrip(self):
        token = uuid.uuid4()
        Product.objects.create(
            price=Money(amount=120, currency="USD"),
            info=Meta(created=date(2021, 6, 1), token=token, label="x"),
            line=Line(qty=2, price=Money(amount=5)),
        )

        with connection.cursor() as cur:
            cur.execute("SELECT data, extra FROM %s" % Product._meta.db_table)
            data_col, extra_col = cur.fetchone()
        self.assertIn('"price"', data_col)
        self.assertIn('"line"', extra_col)

        product = Product.objects.get()
        self.assertEqual(product.price, Money(amount=120, currency="USD"))
        self.assertEqual(product.info.created, date(2021, 6, 1))
        self.assertEqual(product.info.token, token)
        self.assertEqual(product.info.label, "x")
        self.assertEqual(product.line.qty, 2)
        self.assertEqual(product.line.price.amount, 5)

    def test_reload_after_inplace_edit(self):
        product = Product.objects.create(price=Money(amount=1, currency="USD"))
        product.price.amount = 42
        product.save()

        self.assertEqual(Product.objects.get(pk=product.pk).price.amount, 42)


class QueryTest(TestCase):
    def test_filter_by_raw_nested_path(self):
        Product.objects.create(price=Money(amount=50, currency="EUR"))
        Product.objects.create(price=Money(amount=99, currency="USD"))

        self.assertEqual(Product.objects.filter(data__price__amount=99).count(), 1)
        self.assertEqual(Product.objects.filter(data__price__currency="EUR").count(), 1)
