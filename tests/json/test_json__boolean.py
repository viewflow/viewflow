from django.db import models
from django.test import TestCase
from viewflow import jsonstore


class BooleanFieldModel(models.Model):
    data = models.JSONField(default=dict)
    boolean_field = jsonstore.BooleanField(json_field_name='data')
    default_false_field = jsonstore.BooleanField(default=False)


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

    def test_falsy_default_is_applied_when_key_is_absent(self):
        # BooleanField(default=False) used a truthiness check on the
        # default, so a falsy default was silently treated as "no default"
        # and the getter returned None instead of False.
        model = BooleanFieldModel()

        self.assertIs(model.default_false_field, False)
