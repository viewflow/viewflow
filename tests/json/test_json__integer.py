from django.db import models
from django.test import TestCase
from viewflow import jsonstore


class IntegerFieldModel(models.Model):
    data = models.JSONField(default=dict)
    integer_field = jsonstore.IntegerField(null=True)
    default_integer_field = jsonstore.IntegerField(default=42)


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
