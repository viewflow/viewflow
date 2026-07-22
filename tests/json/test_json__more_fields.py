from django.db import models
from django.test import TestCase
from viewflow import jsonstore


class MoreFieldsModel(models.Model):
    data = models.JSONField(default=dict)
    big = jsonstore.BigIntegerField(null=True)
    small = jsonstore.SmallIntegerField(null=True)
    pos = jsonstore.PositiveIntegerField(null=True)
    pos_small = jsonstore.PositiveSmallIntegerField(null=True)
    pos_big = jsonstore.PositiveBigIntegerField(null=True)
    slug = jsonstore.SlugField(max_length=50, null=True)
    fpath = jsonstore.FilePathField(path="/tmp", null=True, blank=True)


class Test(TestCase):
    def test_roundtrip(self):
        MoreFieldsModel.objects.create(
            big=2**40,
            small=7,
            pos=5,
            pos_small=3,
            pos_big=2**50,
            slug="hello-world",
            fpath="/tmp/x",
        )

        obj = MoreFieldsModel.objects.get()
        self.assertEqual(obj.big, 2**40)
        self.assertEqual(obj.small, 7)
        self.assertEqual(obj.pos, 5)
        self.assertEqual(obj.pos_small, 3)
        self.assertEqual(obj.pos_big, 2**50)
        self.assertEqual(obj.slug, "hello-world")
        self.assertEqual(obj.fpath, "/tmp/x")

    def test_integer_variant_orders_numerically(self):
        # the extracted value is sorted, so 2 < 9 < 10 (not the lexical
        # order of the JSON blob's text)
        MoreFieldsModel.objects.create(big=9)
        MoreFieldsModel.objects.create(big=10)
        MoreFieldsModel.objects.create(big=2)

        ordered = list(
            MoreFieldsModel.objects.order_by("big").values_list("big", flat=True)
        )

        self.assertEqual(ordered, [2, 9, 10])
