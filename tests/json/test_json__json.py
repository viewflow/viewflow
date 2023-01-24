from django.db import models
from django.test import TestCase
from viewflow import jsonstore


class JsonFieldModel(models.Model):
    data = models.JSONField(default=dict)
    json_field = jsonstore.JSONField(max_length=250, blank=True)


class Test(TestCase):
    def test_crud(self):
        model = JsonFieldModel(json_field={"test": "value"})
        self.assertIsInstance(model._meta.get_field("json_field"), models.JSONField)
        self.assertEqual(
            model.data,
            {
                "json_field": {"test": "value"},
            },
        )
        model.save()

        model = JsonFieldModel.objects.get()
        self.assertEqual(
            model.data,
            {
                "json_field": {"test": "value"},
            },
        )
        self.assertEqual(model.json_field, {"test": "value"})
