from django.db import models
from django.test import TestCase
from viewflow import jsonstore


class BooleanFieldModel(models.Model):
    data = models.JSONField()
    boolean_field = jsonstore.BooleanField(json_field_name='data')


class Test(TestCase):
    def test_crud(self):
        model = BooleanFieldModel(boolean_field=False)
        self.assertIsInstance(
            model._meta.get_field('boolean_field'),
            models.BooleanField
        )
        self.assertEqual(model.data, {
            'boolean_field': False
        })
        model.save()

        model = BooleanFieldModel.objects.get()
        self.assertEqual(model.data, {
            'boolean_field': False
        })
        self.assertEqual(model.boolean_field, False)
