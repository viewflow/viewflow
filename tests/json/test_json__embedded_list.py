import uuid
from datetime import date

from django.db import connection, models
from django.test import TestCase
from viewflow import jsonstore


class LineItem(jsonstore.EmbeddedModel):
    sku = jsonstore.CharField(max_length=10)
    qty = jsonstore.IntegerField(default=1)


class Event(jsonstore.EmbeddedModel):
    at = jsonstore.DateField(null=True)
    ref = jsonstore.UUIDField(null=True)


class Cart(models.Model):
    data = models.JSONField(default=dict)
    extra = models.JSONField(default=dict)

    lines = jsonstore.EmbeddedListField(LineItem)
    # nested placement
    history = jsonstore.EmbeddedListField(Event, json_key=("audit", "events"))
    # a different column
    archived = jsonstore.EmbeddedListField(LineItem, json_field_name="extra")


class BasicsTest(TestCase):
    def test_empty_by_default(self):
        cart = Cart()

        self.assertEqual(len(cart.lines), 0)
        self.assertEqual(list(cart.lines), [])

    def test_assignment_stores_array(self):
        cart = Cart(lines=[LineItem(sku="a", qty=1), LineItem(sku="b", qty=2)])

        self.assertEqual(
            cart.data,
            {"lines": [{"sku": "a", "qty": 1}, {"sku": "b", "qty": 2}]},
        )

    def test_index_returns_embedded_instance(self):
        cart = Cart(lines=[LineItem(sku="a", qty=1)])

        self.assertIsInstance(cart.lines[0], LineItem)
        self.assertEqual(cart.lines[0].sku, "a")

    def test_iteration_and_len(self):
        cart = Cart(lines=[LineItem(sku=str(i)) for i in range(3)])

        self.assertEqual(len(cart.lines), 3)
        self.assertEqual([item.sku for item in cart.lines], ["0", "1", "2"])

    def test_slice(self):
        cart = Cart(lines=[LineItem(sku=str(i)) for i in range(3)])

        self.assertEqual([item.sku for item in cart.lines[1:]], ["1", "2"])

    def test_dict_elements_accepted(self):
        cart = Cart(lines=[{"sku": "a", "qty": 4}])

        self.assertEqual(cart.lines[0].qty, 4)

    def test_bad_element_raises(self):
        cart = Cart()
        with self.assertRaises(TypeError):
            cart.lines = [123]

    def test_equality(self):
        cart = Cart(lines=[LineItem(sku="a", qty=1)])

        self.assertEqual(list(cart.lines), [LineItem(sku="a", qty=1)])


class MutationTest(TestCase):
    def test_append_and_insert(self):
        cart = Cart(lines=[LineItem(sku="a")])

        cart.lines.append(LineItem(sku="c"))
        cart.lines.insert(1, LineItem(sku="b"))

        self.assertEqual([i.sku for i in cart.lines], ["a", "b", "c"])

    def test_extend(self):
        cart = Cart(lines=[LineItem(sku="a")])

        cart.lines.extend([LineItem(sku="b"), LineItem(sku="c")])

        self.assertEqual([i.sku for i in cart.lines], ["a", "b", "c"])

    def test_setitem(self):
        cart = Cart(lines=[LineItem(sku="a")])

        cart.lines[0] = LineItem(sku="z", qty=9)

        self.assertEqual(cart.data["lines"], [{"sku": "z", "qty": 9}])

    def test_delitem(self):
        cart = Cart(lines=[LineItem(sku="a"), LineItem(sku="b")])

        del cart.lines[0]

        self.assertEqual([i.sku for i in cart.lines], ["b"])

    def test_element_write_through(self):
        cart = Cart(lines=[LineItem(sku="a", qty=1)])

        cart.lines[0].qty = 9

        self.assertEqual(cart.data["lines"][0], {"sku": "a", "qty": 9})
        self.assertEqual(cart.lines[0].qty, 9)

    def test_append_on_fresh_object(self):
        cart = Cart()

        cart.lines.append(LineItem(sku="a"))

        # only explicitly-set fields are stored; qty's default applies on read
        self.assertEqual(cart.data["lines"], [{"sku": "a"}])
        self.assertEqual(cart.lines[0].qty, 1)

    def test_clear_with_empty_list(self):
        cart = Cart(lines=[LineItem(sku="a")])

        cart.lines = []

        self.assertEqual(len(cart.lines), 0)
        self.assertNotIn("lines", cart.data)


class PlacementTest(TestCase):
    def test_nested_placement(self):
        cart = Cart(history=[Event(at=date(2020, 1, 2))])

        self.assertEqual(cart.data["audit"]["events"], [{"at": "2020-01-02"}])

    def test_custom_column(self):
        cart = Cart(archived=[LineItem(sku="old")])

        self.assertEqual(cart.extra, {"archived": [{"sku": "old"}]})
        self.assertEqual(cart.data, {})
        self.assertEqual(cart.archived[0].qty, 1)

    def test_typed_fields_in_elements(self):
        ref = uuid.uuid4()
        cart = Cart(history=[Event(at=date(2021, 6, 1), ref=ref)])

        self.assertEqual(
            cart.data["audit"]["events"], [{"at": "2021-06-01", "ref": str(ref)}]
        )
        self.assertEqual(cart.history[0].at, date(2021, 6, 1))
        self.assertEqual(cart.history[0].ref, ref)
        self.assertIsInstance(cart.history[0].ref, uuid.UUID)


class RoundtripTest(TestCase):
    def test_db_roundtrip(self):
        Cart.objects.create(
            lines=[LineItem(sku="a", qty=2), LineItem(sku="b", qty=3)],
            archived=[LineItem(sku="old")],
        )

        with connection.cursor() as cur:
            cur.execute("SELECT data, extra FROM %s" % Cart._meta.db_table)
            data_col, extra_col = cur.fetchone()
        self.assertIn('"lines"', data_col)
        self.assertIn('"archived"', extra_col)

        cart = Cart.objects.get()
        self.assertEqual([(i.sku, i.qty) for i in cart.lines], [("a", 2), ("b", 3)])
        self.assertEqual([i.sku for i in cart.archived], ["old"])

    def test_reload_after_element_edit(self):
        cart = Cart.objects.create(lines=[LineItem(sku="a", qty=1)])
        cart.lines[0].qty = 42
        cart.save()

        self.assertEqual(Cart.objects.get(pk=cart.pk).lines[0].qty, 42)

    def test_reload_after_append(self):
        cart = Cart.objects.create(lines=[LineItem(sku="a")])
        cart.lines.append(LineItem(sku="b"))
        cart.save()

        self.assertEqual(
            [i.sku for i in Cart.objects.get(pk=cart.pk).lines], ["a", "b"]
        )


class QueryTest(TestCase):
    def test_filter_by_raw_index_path(self):
        Cart.objects.create(lines=[LineItem(sku="a", qty=5)])
        Cart.objects.create(lines=[LineItem(sku="b", qty=9)])

        self.assertEqual(Cart.objects.filter(data__lines__0__sku="a").count(), 1)
