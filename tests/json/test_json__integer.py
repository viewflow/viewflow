from django.db import models
from django.test import TestCase
from viewflow import jsonstore


class IntegerFieldModel(models.Model):
    data = models.JSONField(default=dict)
    integer_field = jsonstore.IntegerField(null=True)
    default_integer_field = jsonstore.IntegerField(default=42)
    default_zero_field = jsonstore.IntegerField(default=0)
    blank_five_field = jsonstore.IntegerField(default=5, blank=True)


class Test(TestCase):
    def test_crud(self):
        model = IntegerFieldModel(integer_field=5)
        self.assertIsInstance(
            model._meta.get_field("integer_field"), models.IntegerField
        )
        self.assertEqual(
            model.data,
            {
                "integer_field": 5,
            },
        )
        model.save()

        model = IntegerFieldModel.objects.get()
        self.assertEqual(
            model.data,
            {
                "integer_field": 5,
            },
        )
        self.assertEqual(model.integer_field, 5)

    def test_null_value(self):
        model = IntegerFieldModel()
        self.assertEqual(model.integer_field, None)
        self.assertEqual(model.data, {})

    def test_default_value(self):
        model = IntegerFieldModel()
        self.assertEqual(model.default_integer_field, 42)

    def test_falsy_default_is_applied_when_key_is_absent(self):
        # IntegerField(default=0) used a truthiness check on the default,
        # so a falsy default (0) was silently treated as "no default" and
        # the getter returned None instead of 0.
        model = IntegerFieldModel()

        self.assertEqual(model.default_zero_field, 0)

    def test_setting_a_falsy_value_does_not_fall_back_to_default(self):
        # __set__ deleted the key whenever the *assigned* value was falsy
        # (not just None/"") on a blank=True, null=False field, so
        # `obj.n = 0` on a field with a non-zero default read back the
        # default instead of the 0 actually assigned.
        model = IntegerFieldModel(blank_five_field=0)

        self.assertEqual(model.data, {"blank_five_field": 0})
        self.assertEqual(model.blank_five_field, 0)

    def test_order_by_sorts_by_the_extracted_value_not_the_raw_json_blob(self):
        # jsonstore fields have self.column = self.json_field_name (the
        # underlying JSONField's real column), and Field.get_col() (the
        # default implementation) built a plain Col referencing that raw
        # column. That's fine for a plain SELECT, where the Python-side
        # convert_json_value converter extracts the value after fetch --
        # but ORDER BY sorts in the database, before any Python conversion
        # runs, so it sorted rows by the whole JSON blob's text
        # representation instead of the extracted integer_field value.
        # 9 vs 10/2: numeric order (2, 9, 10) differs from the lexicographic
        # order of the JSON blob's text (`{"integer_field": 10}` sorts
        # before `{"integer_field": 2}` sorts before `{"integer_field": 9}`).
        IntegerFieldModel.objects.create(integer_field=9)
        IntegerFieldModel.objects.create(integer_field=10)
        IntegerFieldModel.objects.create(integer_field=2)

        ordered = list(
            IntegerFieldModel.objects.order_by("integer_field").values_list(
                "integer_field", flat=True
            )
        )

        self.assertEqual(ordered, [2, 9, 10])
