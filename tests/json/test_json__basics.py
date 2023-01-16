from unittest import skipUnless
from django import forms
from django.db import connection, models
from django.test import TestCase, override_settings
from viewflow import jsonstore


skipIfNoJson = skipUnless(
    connection.vendor in ["postgresql", "mysql", "oracle"],
    "Databases with first-class JSONField support",
)


@override_settings(DEBUG=True)
class Test(TestCase):
    def test_managers_api(self):
        Person.objects.create(data={"name": "John Doe"})
        self.assertEqual(Person.objects.first().data, {"name": "John Doe"})

    def test_model_api(self):
        person = Person(name="John Doe")
        self.assertEqual(person.name, "John Doe")
        self.assertEqual(person.data, {"name": "John Doe"})

        person.save()
        person.refresh_from_db()

        self.assertEqual(person.name, "John Doe")
        self.assertEqual(person.data, {"name": "John Doe"})

    def test_forms_api(self):
        form = PersonForm()
        self.assertIn("name", form.fields)

        form = ClientForm()
        self.assertIn("name", form.fields, "Inherited field 'name' not found")

        form = VIPClientForm()
        self.assertIn("name", form.fields, "Inherited field name not found")
        # self.assertIn('personal_phone', form.fields, "Field 'personal_phone' not found")

    @skipIfNoJson
    def test_iexact_query(self):
        Person.objects.create(name="John Doe")
        Person.objects.create(name="Will Smith")

        person = Person.objects.get(name="John Doe")
        self.assertEqual(person.name, "John Doe")

    @skipIfNoJson
    def test_isnull_query(self):
        Person.objects.create(name="John Doe")
        Person.objects.create(name="Will Smith")

        persons = Person.objects.filter(name__isnull=True)
        self.assertEqual(0, persons.count())
        persons = Person.objects.filter(name__isnull=False)
        self.assertEqual(2, persons.count())

    def test_values_list(self):
        Person.objects.create(name="John Doe", address="New York")
        Person.objects.create(name="Will Smith", address="Washington")

        data = Person.objects.values_list("name")

        self.assertEqual(
            list(data),
            [("John Doe",), ("Will Smith",)],
        )

    def test_values(self):
        Person.objects.create(name="John Doe", address="New York")
        Person.objects.create(name="Will Smith", address="Washington")

        data = Person.objects.values("name")

        self.assertEqual(
            list(data),
            [{"name": "John Doe"}, {"name": "Will Smith"}],
        )


class Person(models.Model):
    data = models.JSONField()
    name = jsonstore.CharField(max_length=250)
    address = jsonstore.CharField(max_length=250, blank=True)


class Client(Person):
    birthdate = jsonstore.DateField()
    business_phone = jsonstore.CharField(max_length=250)


class VIPClient(Client):
    approved = jsonstore.BooleanField()
    personal_phone = jsonstore.CharField(max_length=250)

    class Meta:
        proxy = True


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        exclude = ["data"]


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        exclude = ["data"]


class VIPClientForm(forms.ModelForm):
    class Meta:
        model = VIPClient
        exclude = ["data"]
