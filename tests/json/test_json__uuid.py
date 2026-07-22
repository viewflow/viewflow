import uuid

from django.db import models
from django.test import TestCase
from viewflow import jsonstore


class UUIDFieldModel(models.Model):
    data = models.JSONField(default=dict)
    uid = jsonstore.UUIDField(null=True)


class Test(TestCase):
    def test_roundtrip(self):
        value = uuid.uuid4()
        UUIDFieldModel.objects.create(uid=value)

        obj = UUIDFieldModel.objects.get()
        # stored JSON-native (a string), read back as a UUID
        self.assertEqual(obj.data, {"uid": str(value)})
        self.assertEqual(obj.uid, value)
        self.assertIsInstance(obj.uid, uuid.UUID)

    def test_none(self):
        obj = UUIDFieldModel()

        self.assertIsNone(obj.uid)
        self.assertEqual(obj.data, {})

    def test_assign_string_form(self):
        value = uuid.uuid4()
        obj = UUIDFieldModel(uid=str(value))
        obj.save()

        self.assertEqual(obj.data, {"uid": str(value)})
        self.assertEqual(UUIDFieldModel.objects.get().uid, value)
