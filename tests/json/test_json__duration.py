from datetime import timedelta

from django.db import models
from django.test import TestCase
from viewflow import jsonstore


class DurationFieldModel(models.Model):
    data = models.JSONField(default=dict)
    dur = jsonstore.DurationField(null=True)


class Test(TestCase):
    def test_roundtrip(self):
        DurationFieldModel.objects.create(dur=timedelta(hours=1, minutes=30))

        obj = DurationFieldModel.objects.get()
        # stored as an ISO-8601 duration string, read back as a timedelta
        self.assertEqual(obj.data, {"dur": "P0DT01H30M00S"})
        self.assertEqual(obj.dur, timedelta(hours=1, minutes=30))
        self.assertIsInstance(obj.dur, timedelta)

    def test_none(self):
        obj = DurationFieldModel()

        self.assertIsNone(obj.dur)
        self.assertEqual(obj.data, {})
