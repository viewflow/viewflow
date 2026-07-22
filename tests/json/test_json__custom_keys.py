import uuid
from datetime import date

from django.db import connection, models
from django.test import TestCase
from viewflow import jsonstore


class CustomKeyModel(models.Model):
    data = models.JSONField(default=dict)
    meta = models.JSONField(default=dict)

    # custom leaf key: stored under data["name"], not data["full_name"]
    full_name = jsonstore.CharField(max_length=50, json_key="name", null=True)

    # nested paths sharing a parent dict: data["address"]["city"/"zip"]
    city = jsonstore.CharField(max_length=50, json_key=("address", "city"), null=True)
    zip_code = jsonstore.CharField(
        max_length=10, json_key=["address", "zip"], null=True
    )

    # nested typed fields exercising to_json/from_json at depth
    age = jsonstore.IntegerField(json_key=("profile", "age"), null=True)
    born = jsonstore.DateField(json_key=("profile", "born"), null=True)
    token = jsonstore.UUIDField(json_key=("profile", "token"), null=True)

    # a different JSON column entirely
    note = jsonstore.CharField(max_length=50, json_field_name="meta", null=True)

    # custom key with a default, and a blank field
    role = jsonstore.CharField(max_length=20, json_key="r", default="user")
    nickname = jsonstore.CharField(
        max_length=20, json_key=("profile", "nick"), blank=True
    )


class StorageTest(TestCase):
    def test_custom_leaf_key(self):
        obj = CustomKeyModel(full_name="Ann")

        self.assertEqual(obj.data, {"name": "Ann"})
        self.assertEqual(obj.full_name, "Ann")

    def test_nested_path_creates_parent(self):
        obj = CustomKeyModel(city="Paris", age=30)

        self.assertEqual(
            obj.data, {"address": {"city": "Paris"}, "profile": {"age": 30}}
        )

    def test_fields_share_a_parent_dict(self):
        obj = CustomKeyModel(city="Paris", zip_code="75001")

        self.assertEqual(obj.data, {"address": {"city": "Paris", "zip": "75001"}})

    def test_custom_json_column(self):
        obj = CustomKeyModel(note="hi", full_name="Ann")

        self.assertEqual(obj.meta, {"note": "hi"})
        self.assertEqual(obj.data, {"name": "Ann"})

    def test_typed_fields_serialize_at_depth(self):
        token = uuid.uuid4()
        obj = CustomKeyModel(age=30, born=date(1990, 1, 2), token=token)

        self.assertEqual(
            obj.data,
            {
                "profile": {
                    "age": 30,
                    "born": "1990-01-02",
                    "token": str(token),
                }
            },
        )

    def test_missing_nested_parent_reads_none(self):
        obj = CustomKeyModel(data={})

        self.assertIsNone(obj.city)
        self.assertIsNone(obj.age)

    def test_default_at_custom_key_when_absent(self):
        obj = CustomKeyModel(data={})

        self.assertEqual(obj.role, "user")

    def test_blank_clears_the_leaf_only(self):
        obj = CustomKeyModel(city="Paris", nickname="Annie")
        self.assertEqual(obj.data["profile"], {"nick": "Annie"})

        obj.nickname = ""

        # only the leaf is removed; the shared parent survives
        self.assertNotIn("nick", obj.data.get("profile", {}))
        self.assertEqual(obj.city, "Paris")


class RoundtripTest(TestCase):
    def test_db_roundtrip(self):
        token = uuid.uuid4()
        CustomKeyModel.objects.create(
            full_name="Ann",
            city="Paris",
            zip_code="75001",
            age=30,
            born=date(1990, 1, 2),
            token=token,
            note="vip",
        )

        # persisted shape in the actual columns
        with connection.cursor() as cur:
            cur.execute("SELECT data, meta FROM %s" % CustomKeyModel._meta.db_table)
            data_col, meta_col = cur.fetchone()

        obj = CustomKeyModel.objects.get()
        self.assertEqual(obj.full_name, "Ann")
        self.assertEqual(obj.city, "Paris")
        self.assertEqual(obj.zip_code, "75001")
        self.assertEqual(obj.age, 30)
        self.assertEqual(obj.born, date(1990, 1, 2))
        self.assertEqual(obj.token, token)
        self.assertIsInstance(obj.token, uuid.UUID)
        self.assertEqual(obj.note, "vip")
        self.assertIn('"address"', data_col)
        self.assertIn('"note"', meta_col)


class QueryTest(TestCase):
    def setUp(self):
        CustomKeyModel.objects.create(full_name="Ann", city="Paris", age=30)
        CustomKeyModel.objects.create(full_name="Bob", city="Lyon", age=10)
        CustomKeyModel.objects.create(full_name="Cid", city="Paris", age=20)

    def _names(self, qs):
        return sorted(qs.values_list("full_name", flat=True))

    def test_exact_by_custom_key(self):
        self.assertEqual(CustomKeyModel.objects.get(full_name="Ann").city, "Paris")

    def test_filter_nested_exact(self):
        self.assertEqual(
            self._names(CustomKeyModel.objects.filter(city="Paris")), ["Ann", "Cid"]
        )

    def test_filter_nested_lookup(self):
        self.assertEqual(
            self._names(CustomKeyModel.objects.filter(age__gt=15)), ["Ann", "Cid"]
        )

    def test_filter_nested_isnull(self):
        CustomKeyModel.objects.create(full_name="Dot")  # no city/age
        self.assertEqual(
            self._names(CustomKeyModel.objects.filter(city__isnull=True)), ["Dot"]
        )

    def test_order_by_nested_is_numeric(self):
        ordered = list(
            CustomKeyModel.objects.order_by("age").values_list("age", flat=True)
        )
        self.assertEqual(ordered, [10, 20, 30])


class CkAuthor(models.Model):
    name = models.CharField(max_length=50)


class CkTag(models.Model):
    name = models.CharField(max_length=50)


class RelationKeyModel(models.Model):
    data = models.JSONField(default=dict)
    # FK stored at a nested/custom key
    author = jsonstore.ForeignKey(
        CkAuthor, json_key=("rel", "author_id"), null=True, blank=True
    )
    # M2M stored at a nested key
    tags = jsonstore.ManyToManyField(CkTag, json_key=("rel", "tag_ids"))


class RelationKeyTest(TestCase):
    def test_foreignkey_nested_key(self):
        author = CkAuthor.objects.create(name="Ann")
        obj = RelationKeyModel.objects.create(author=author)

        self.assertEqual(obj.data, {"rel": {"author_id": author.pk}})
        fresh = RelationKeyModel.objects.get(pk=obj.pk)
        self.assertEqual(fresh.author, author)
        self.assertEqual(fresh.author_id, author.pk)

    def test_manytomany_nested_key(self):
        t1 = CkTag.objects.create(name="a")
        t2 = CkTag.objects.create(name="b")
        obj = RelationKeyModel.objects.create()
        obj.tags.set([t1, t2])
        obj.save()

        self.assertEqual(obj.data, {"rel": {"tag_ids": [t1.pk, t2.pk]}})
        fresh = RelationKeyModel.objects.get(pk=obj.pk)
        self.assertEqual(
            sorted(fresh.tags.all().values_list("name", flat=True)), ["a", "b"]
        )

    def test_relations_can_share_a_parent(self):
        author = CkAuthor.objects.create(name="Ann")
        tag = CkTag.objects.create(name="a")
        obj = RelationKeyModel.objects.create(author=author)
        obj.tags.set([tag])
        obj.save()

        self.assertEqual(
            obj.data, {"rel": {"author_id": author.pk, "tag_ids": [tag.pk]}}
        )
