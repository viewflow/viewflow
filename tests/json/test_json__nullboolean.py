from django.db import models
from django.test import TestCase
from viewflow import jsonstore


class NullBooleanFieldModel(models.Model):
    data = models.JSONField()
    nullboolean_field = jsonstore.NullBooleanField()


class Test(TestCase):
    def test_crud(self):
        model = NullBooleanFieldModel(nullboolean_field=False)
        self.assertIsInstance(
            model._meta.get_field('nullboolean_field'),
            models.NullBooleanField
        )
        self.assertEqual(model.data, {
            'nullboolean_field': False
        })
        model.save()

        model = NullBooleanFieldModel.objects.get()
        self.assertEqual(model.data, {
            'nullboolean_field': False
        })
        self.assertEqual(model.nullboolean_field, False)

    def test_null_value(self):
        model = NullBooleanFieldModel(nullboolean_field=None)
        self.assertEqual(model.nullboolean_field, None)
        self.assertEqual(model.data, {
            'nullboolean_field': None
        })
