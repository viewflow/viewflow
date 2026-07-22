import uuid

from django import forms
from django.db import models
from django.forms.models import ModelChoiceField
from django.test import TestCase
from viewflow import jsonstore


class Author(models.Model):
    name = models.CharField(max_length=50)


class UUIDAuthor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)


class Publisher(models.Model):
    name = models.CharField(max_length=50)


class Book(models.Model):
    data = models.JSONField(default=dict)
    title = jsonstore.CharField(max_length=50)
    author = jsonstore.ForeignKey(Author, null=True, blank=True)
    # a lazy "app.Model" reference must resolve too
    publisher = jsonstore.ForeignKey("tests.Publisher", null=True, blank=True)


class UUIDBook(models.Model):
    data = models.JSONField(default=dict)
    author = jsonstore.ForeignKey(UUIDAuthor, null=True, blank=True)


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ("title", "author")


class Test(TestCase):
    def test_stores_pk_in_json_blob(self):
        author = Author.objects.create(name="Ann")
        book = Book(title="T", author=author)

        self.assertEqual(book.data, {"title": "T", "author_id": author.pk})
        self.assertEqual(book.author_id, author.pk)

    def test_roundtrip_loads_related_object(self):
        author = Author.objects.create(name="Ann")
        Book.objects.create(title="T", author=author)

        book = Book.objects.get()
        self.assertEqual(book.data, {"title": "T", "author_id": author.pk})
        self.assertEqual(book.author, author)
        self.assertEqual(book.author.name, "Ann")

    def test_no_author_is_none(self):
        book = Book(title="X")

        self.assertIsNone(book.author)
        self.assertNotIn("author_id", book.data)

    def test_assigning_none_clears_it(self):
        author = Author.objects.create(name="Ann")
        book = Book(title="T", author=author)

        book.author = None

        self.assertIsNone(book.author)
        self.assertIsNone(book.author_id)

    def test_assign_by_raw_id(self):
        author = Author.objects.create(name="Ann")
        book = Book(title="T")

        book.author_id = author.pk

        self.assertEqual(book.data, {"title": "T", "author_id": author.pk})
        self.assertEqual(book.author, author)

    def test_cache_invalidated_when_id_changes(self):
        ann = Author.objects.create(name="Ann")
        bob = Author.objects.create(name="Bob")
        book = Book(title="T", author=ann)
        self.assertEqual(book.author, ann)  # primes the cache

        book.author_id = bob.pk

        self.assertEqual(book.author, bob)

    def test_lazy_string_reference_resolves(self):
        pub = Publisher.objects.create(name="P")
        Book.objects.create(title="T", publisher=pub)

        book = Book.objects.get()
        self.assertEqual(book.publisher, pub)

    def test_filter_by_json_key(self):
        author = Author.objects.create(name="Ann")
        Book.objects.create(title="A", author=author)
        Book.objects.create(title="B")

        found = Book.objects.filter(data__author_id=author.pk)

        self.assertEqual([b.title for b in found], ["A"])

    def test_formfield_is_model_choice_field(self):
        field = Book._meta.get_field("author").formfield()

        self.assertIsInstance(field, ModelChoiceField)
        self.assertEqual(list(field.queryset), list(Author.objects.all()))

    def test_modelform_saves_relation(self):
        author = Author.objects.create(name="Ann")
        form = BookForm(data={"title": "T", "author": str(author.pk)})

        self.assertTrue(form.is_valid(), form.errors)
        book = form.save()

        self.assertEqual(book.author, author)
        self.assertEqual(Book.objects.get().data["author_id"], author.pk)

    def test_modelform_edit_prefills_and_updates(self):
        ann = Author.objects.create(name="Ann")
        bob = Author.objects.create(name="Bob")
        book = Book.objects.create(title="T", author=ann)

        # a bound-to-instance edit form pre-selects the current relation
        edit = BookForm(instance=book)
        self.assertEqual(edit["author"].value(), ann.pk)

        # and can change it
        changed = BookForm(data={"title": "T", "author": str(bob.pk)}, instance=book)
        self.assertTrue(changed.is_valid(), changed.errors)
        changed.save()
        self.assertEqual(Book.objects.get(pk=book.pk).author, bob)

    def test_modelform_can_clear_optional_relation(self):
        ann = Author.objects.create(name="Ann")
        book = Book.objects.create(title="T", author=ann)

        form = BookForm(data={"title": "T", "author": ""}, instance=book)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.assertIsNone(Book.objects.get(pk=book.pk).author)

    def test_foreignkey_to_uuid_pk_model(self):
        # a target model with a UUID primary key: the pk isn't JSON-native,
        # so it's stored as its string form and coerced back to a UUID.
        author = UUIDAuthor.objects.create(name="Ann")
        UUIDBook.objects.create(author=author)

        book = UUIDBook.objects.get()
        self.assertEqual(book.data, {"author_id": str(author.pk)})
        self.assertEqual(book.author, author)
        self.assertIsInstance(book.author_id, uuid.UUID)
        # queryable through the JSON key (string form)
        self.assertEqual(
            UUIDBook.objects.filter(data__author_id=str(author.pk)).count(), 1
        )
