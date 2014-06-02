from django.test import TestCase
from django.contrib.auth.models import Permission

from unit.models import TestProcess


class TestAutoPermissionsFlow(TestCase):
    def test_permission_created(self):
        permission = Permission.objects.get(codename='can_start_testprocess')
        self.assertEqual(TestProcess, permission.content_type.model_class())
