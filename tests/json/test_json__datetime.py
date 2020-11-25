from django.db import models
from django.test import TestCase
from django.utils import timezone
from viewflow import jsonstore


class DateTimeFieldModel(models.Model):
    data = models.JSONField()
    datetime_field = jsonstore.DateTimeField(blank=True, null=False)


class Test(TestCase):
    def test_crud(self):
        model = DateTimeFieldModel(datetime_field=timezone.datetime(2020, 1, 31, 12, 59, 3))
        self.assertIsInstance(
            model._meta.get_field('datetime_field'),
            models.DateTimeField
        )
        self.assertEqual(model.data, {
            'datetime_field': '2020-01-31T12:59:03+00:00'
        })
        model.save()

        model = DateTimeFieldModel.objects.get()
        self.assertEqual(model.data, {
            'datetime_field': '2020-01-31T12:59:03+00:00'
        })
        self.assertEqual(
            model.datetime_field,
            timezone.make_aware(timezone.datetime(2020, 1, 31, 12, 59, 3)))

    def test_null_value(self):
        model = DateTimeFieldModel(datetime_field=None)
        self.assertEqual(model.datetime_field, None)
        self.assertEqual(model.data, {})
