import uuid

from django import forms
from django.db import models
from django.forms.models import ModelMultipleChoiceField
from django.test import TestCase
from viewflow import jsonstore


class Tag(models.Model):
    name = models.CharField(max_length=50)


class UUIDTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)


class Post(models.Model):
    data = models.JSONField(default=dict)
    title = jsonstore.CharField(max_length=50)
    tags = jsonstore.ManyToManyField(Tag)
    uuid_tags = jsonstore.ManyToManyField(UUIDTag)


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("title", "tags")


class Test(TestCase):
    def setUp(self):
        self.t1 = Tag.objects.create(name="a")
        self.t2 = Tag.objects.create(name="b")
        self.t3 = Tag.objects.create(name="c")

    def _names(self, post):
        return sorted(post.tags.all().values_list("name", flat=True))

    def test_set_stores_pk_list(self):
        post = Post.objects.create(title="T")
        post.tags.set([self.t1, self.t2])

        self.assertEqual(post.data, {"title": "T", "tags": [self.t1.pk, self.t2.pk]})

    def test_roundtrip(self):
        post = Post.objects.create(title="T")
        post.tags.set([self.t1, self.t2])
        post.save()

        fresh = Post.objects.get(pk=post.pk)
        self.assertEqual(self._names(fresh), ["a", "b"])
        self.assertEqual(fresh.tags.count(), 2)

    def test_add_dedupes_and_remove(self):
        post = Post.objects.create(title="T")
        post.tags.set([self.t1])
        post.tags.add(self.t1, self.t2)  # t1 already present
        self.assertEqual(self._names(post), ["a", "b"])

        post.tags.remove(self.t1)
        self.assertEqual(self._names(post), ["b"])

    def test_clear(self):
        post = Post.objects.create(title="T")
        post.tags.set([self.t1, self.t2])

        post.tags.clear()

        self.assertEqual(post.tags.count(), 0)
        self.assertNotIn("tags", post.data)

    def test_direct_assignment(self):
        post = Post.objects.create(title="T")
        post.tags = [self.t1, self.t2]

        self.assertEqual(self._names(post), ["a", "b"])

    def test_empty_manager_returns_no_objects(self):
        post = Post.objects.create(title="T")

        self.assertEqual(list(post.tags.all()), [])
        self.assertEqual(post.tags.count(), 0)

    def test_formfield_is_model_multiple_choice(self):
        field = Post._meta.get_field("tags").formfield()

        self.assertIsInstance(field, ModelMultipleChoiceField)

    def test_modelform_create_edit_clear(self):
        form = PostForm(data={"title": "T", "tags": [str(self.t1.pk), str(self.t2.pk)]})
        self.assertTrue(form.is_valid(), form.errors)
        post = form.save()
        self.assertEqual(self._names(Post.objects.get(pk=post.pk)), ["a", "b"])

        # edit down to one
        edit = PostForm(data={"title": "T", "tags": [str(self.t1.pk)]}, instance=post)
        self.assertTrue(edit.is_valid(), edit.errors)
        edit.save()
        self.assertEqual(self._names(Post.objects.get(pk=post.pk)), ["a"])

        # a bound edit form pre-selects the current selection
        self.assertEqual(
            PostForm(instance=Post.objects.get(pk=post.pk))["tags"].value(),
            [self.t1.pk],
        )

        # clear
        clear = PostForm(data={"title": "T", "tags": []}, instance=post)
        self.assertTrue(clear.is_valid(), clear.errors)
        clear.save()
        self.assertEqual(Post.objects.get(pk=post.pk).tags.count(), 0)

    def test_uuid_pk_targets(self):
        u1 = UUIDTag.objects.create(name="x")
        u2 = UUIDTag.objects.create(name="y")
        post = Post.objects.create(title="T")
        post.uuid_tags.set([u1, u2])
        post.save()

        fresh = Post.objects.get(pk=post.pk)
        # stored as JSON-native strings
        self.assertEqual(fresh.data["uuid_tags"], [str(u1.pk), str(u2.pk)])
        self.assertEqual(
            sorted(fresh.uuid_tags.all().values_list("name", flat=True)), ["x", "y"]
        )
