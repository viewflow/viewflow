from django import forms
from django.db import models
from django.forms.models import ModelChoiceField
from django.test import TestCase
from viewflow import jsonstore


class Profile(models.Model):
    name = models.CharField(max_length=50)


class Account(models.Model):
    data = models.JSONField(default=dict)
    profile = jsonstore.OneToOneField(Profile, null=True, blank=True)


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ("profile",)


class Test(TestCase):
    def test_roundtrip(self):
        profile = Profile.objects.create(name="Ann")
        Account.objects.create(profile=profile)

        account = Account.objects.get()
        self.assertEqual(account.data, {"profile_id": profile.pk})
        self.assertEqual(account.profile, profile)
        self.assertEqual(account.profile_id, profile.pk)

    def test_none(self):
        account = Account(data={})

        self.assertIsNone(account.profile)

    def test_formfield_is_model_choice_field(self):
        field = Account._meta.get_field("profile").formfield()

        self.assertIsInstance(field, ModelChoiceField)

    def test_modelform_create_and_edit(self):
        ann = Profile.objects.create(name="Ann")
        bob = Profile.objects.create(name="Bob")

        form = AccountForm(data={"profile": str(ann.pk)})
        self.assertTrue(form.is_valid(), form.errors)
        account = form.save()
        self.assertEqual(Account.objects.get(pk=account.pk).profile, ann)

        # a bound edit form pre-selects the relation and can change it
        self.assertEqual(AccountForm(instance=account)["profile"].value(), ann.pk)
        changed = AccountForm(data={"profile": str(bob.pk)}, instance=account)
        self.assertTrue(changed.is_valid(), changed.errors)
        changed.save()
        self.assertEqual(Account.objects.get(pk=account.pk).profile, bob)
