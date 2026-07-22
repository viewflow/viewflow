from django.db import models
from django.test import TestCase
from viewflow import jsonstore


class BinaryFieldModel(models.Model):
    data = models.JSONField(default=dict)
    blob = jsonstore.BinaryField(null=True, blank=True)


class Test(TestCase):
    def test_roundtrip(self):
        raw = b"\x00\x01\x02hello\xff"
        BinaryFieldModel.objects.create(blob=raw)

        obj = BinaryFieldModel.objects.get()
        # stored base64-encoded, read back as bytes
        self.assertEqual(obj.data, {"blob": "AAECaGVsbG//"})
        self.assertEqual(obj.blob, raw)
        self.assertIsInstance(obj.blob, bytes)

    def test_none(self):
        obj = BinaryFieldModel()

        self.assertIsNone(obj.blob)
        self.assertEqual(obj.data, {})
