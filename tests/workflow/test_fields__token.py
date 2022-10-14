from django import forms
from django.db import models
from django.test import TestCase, tag
from viewflow.workflow.token import Token
from viewflow.workflow.fields import TokenField


@tag('integration')
class Test(TestCase):  # noqa: D101
    def test_crud(self):
        obj = TokenTestModel.objects.create(token=Token('start'))
        self.assertEqual(obj.token, Token('start'))

        obj = TokenTestModel.objects.get()
        self.assertEqual(obj.token, Token('start'))

        obj = TokenTestModel.objects.filter(token=Token('start')).first()
        self.assertEqual(obj.token, Token('start'))

    def test_forms(self):
        form = TokenTestForm(data={'token': 'start'})
        form.is_valid()
        obj = form.save()

        self.assertEqual(obj.token, Token('start'))


class TokenTestModel(models.Model):  # noqa: D101
    token = TokenField()


class TokenTestForm(forms.ModelForm):  # noqa: D101
    class Meta:
        model = TokenTestModel
        fields = ('token', )

