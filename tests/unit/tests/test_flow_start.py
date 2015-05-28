from django.contrib.auth.models import User
from django.test import TestCase
from viewflow import flow


class Test(TestCase):
    def test_available_callable(self):
        start = flow.Start().Available(lambda u: u.username.startswith('allowed'))
        self.privileged_user = User.objects.create_superuser('allowed', 'admin@admin.com', 'allowed')
        self.unprivileged_user = User.objects.create_superuser('admin', 'admin@admin.com', 'admin')

        self.assertTrue(start.can_execute(self.privileged_user))
        self.assertFalse(start.can_execute(self.unprivileged_user))
