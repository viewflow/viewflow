# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

import base64
import collections.abc
import copy
import json
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from functools import partialmethod

from django.core.exceptions import FieldError
from django.db.models import fields, DEFERRED, DO_NOTHING
from django.db.models import ForeignKey as BaseForeignKey
from django.db.models import JSONField as BaseJSONField
from django.db.models import ManyToManyField as BaseManyToManyField
from django.db.models.fields.related import lazy_related_operation
from django.utils import dateparse, timezone
from django.utils.duration import duration_iso_string


DEFAULT = object()


def _json_resolve(root, path, create=False):
    """Walk ``path`` (a tuple of keys) inside the ``root`` dict.

    Returns ``(container, leaf_key)`` where ``container[leaf_key]`` is the
    stored slot. With ``create=False`` a missing (or non-dict) intermediate
    yields ``(None, leaf_key)``; with ``create=True`` intermediate dicts are
    created as needed so the slot can be written.
    """
    container = root
    for key in path[:-1]:
        nxt = container.get(key) if isinstance(container, dict) else None
        if not isinstance(nxt, dict):
            if not create:
                return None, path[-1]
            nxt = {}
            container[key] = nxt
        container = nxt
    return container, path[-1]


class JSONFieldDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        json_value = getattr(instance, self.field.json_field_name)
        if isinstance(json_value, dict):
            container, leaf = _json_resolve(json_value, self.field.json_path)
            if isinstance(container, dict) and leaf in container:
                value = container.get(leaf, None)
                if hasattr(self.field, "from_json"):
                    value = self.field.from_json(value)
            elif self.field.default is not fields.NOT_PROVIDED:
                if callable(self.field.default):
                    value = self.field.default()
                else:
                    value = self.field.default
            else:
                value = None
            return value
        return None

    def __set__(self, instance, value):
        json_value = getattr(instance, self.field.json_field_name)
        if json_value:
            assert isinstance(json_value, dict)
        else:
            json_value = {}

        if hasattr(self.field, "to_json"):
            value = self.field.to_json(value)

        container, leaf = _json_resolve(json_value, self.field.json_path, create=True)
        if (value is None or value == "") and self.field.blank and not self.field.null:
            container.pop(leaf, None)
        else:
            container[leaf] = value

        setattr(instance, self.field.json_field_name, json_value)


class ForeignObjectDescriptor(object):
    """Access the related object of a jsonstore :class:`ForeignKey`.

    The related object's primary key is kept in the JSON blob under the
    field's ``attname`` (e.g. ``author_id``); the object itself is fetched
    lazily on first access and cached on the instance. Assigning an object
    stores its pk, assigning ``None`` clears it.
    """

    def __init__(self, field):
        self.field = field
        self.cache_name = "_jsonstore_%s_cache" % field.name

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        pk = getattr(instance, self.field.attname)
        if pk is None:
            return None
        if hasattr(instance, self.cache_name):
            cached = getattr(instance, self.cache_name)
            # keep the cache only while it still matches the stored id
            if cached is not None and cached.pk == pk:
                return cached
        obj = self.field.related_model._base_manager.filter(pk=pk).first()
        setattr(instance, self.cache_name, obj)
        return obj

    def __set__(self, instance, value):
        if value is None:
            setattr(instance, self.field.attname, None)
            if hasattr(instance, self.cache_name):
                delattr(instance, self.cache_name)
            return
        setattr(instance, self.field.attname, value.pk)
        setattr(instance, self.cache_name, value)


class JSONFieldMixin(object):
    """
        Override django.db.model.fields.Field.contribute_to_class
    to make a field always private, and register custom access descriptor
    """

    def __init__(self, *args, **kwargs):
        self.json_field_name = kwargs.pop("json_field_name", "data")
        # Where inside the JSON document the value is stored. By default the
        # field's ``attname``; override with ``json_key`` to use a custom key
        # (a string) or a nested path (a list/tuple of keys), e.g.
        # ``json_key="full_name"`` -> ``data["full_name"]`` or
        # ``json_key=("profile", "name")`` -> ``data["profile"]["name"]``.
        self.json_key = kwargs.pop("json_key", None)
        super(JSONFieldMixin, self).__init__(*args, **kwargs)

    @property
    def json_path(self):
        key = self.json_key
        if key is None:
            return (self.attname,)
        if isinstance(key, (list, tuple)):
            return tuple(str(part) for part in key) or (self.attname,)
        return (str(key),)

    def contribute_to_class(self, cls, name, private_only=False):
        self.set_attributes_from_name(name)
        self.model = cls
        self.concrete = False
        self.column = None  # self.json_field_name
        cls._meta.add_field(self, private=True)

        if not getattr(cls, self.attname, None):
            descriptor = JSONFieldDescriptor(self)
            setattr(cls, self.attname, descriptor)

        if self.choices is not None:
            setattr(
                cls,
                "get_%s_display" % self.name,
                partialmethod(cls._get_FIELD_display, field=self),
            )

        self.column = self.json_field_name

        # def on_model_init(sender, name=name, **kwargs):
        #     """ Initialize default values """
        #     instance = kwargs['instance']
        #     if getattr(instance, name) is None:
        #         field = instance._meta.get_field(name)
        #         if not field.null:
        #             setattr(instance, name, field.get_default())

        # post_init.connect(on_model_init, sender=cls, weak=False)

    # tOod why?
    def get_default(self):
        return DEFERRED

    def get_lookup(self, lookup_name):
        # Always return None, to make get_transform been called
        return None

    def get_col(self, alias, output_field=None):
        # Route plain field references (e.g. order_by("field")) through the
        # same key-transform SQL used for filtering, instead of a bare Col
        # referencing the raw JSONField column -- otherwise ordering sorts
        # by the JSON blob's text representation, not the extracted value.
        # Chain one key transform per element of json_path for nested keys.
        json_field = self.model._meta.get_field(self.json_field_name)
        result = json_field.get_col(alias)
        for key in self.json_path:
            transform_class = json_field.get_transform(key)
            if transform_class is None:
                return super().get_col(alias, output_field)
            result = transform_class(result)
        return result

    def formfield(self, **kwargs):
        if self.has_default():
            if not callable(self.default):
                kwargs["initial"] = self._get_default()
        return super().formfield(**kwargs)

    def get_transform(self, name):
        json_field = self.model._meta.get_field(self.json_field_name)
        path = self.json_path

        for key in path:
            if json_field.get_transform(key) is None:
                raise FieldError(
                    "JSONField '%s' has no support for key '%s' %s lookup"
                    % (self.json_field_name, key, name)
                )

        class NestedTransformFactory:
            """Apply one key transform per json_path element, forcing the
            requested lookup/transform (``name``) on the leaf key."""

            def __call__(self, lhs, **kwargs):
                result = copy.copy(lhs)
                result.target = json_field
                result.output_field = json_field
                # nested keys: plain key transforms, still JSON-typed so the
                # next key can be extracted
                for key in path[:-1]:
                    result = json_field.get_transform(key)(result)
                    result = copy.copy(result)
                    result.target = json_field
                    result.output_field = json_field
                transform = json_field.get_transform(path[-1])(result, **kwargs)
                transform._original_get_lookup = transform.get_lookup
                transform.get_lookup = lambda n: transform._original_get_lookup(name)
                return transform

        return NestedTransformFactory()

    def convert_json_value(self, value, expression, connection):
        if isinstance(value, str):
            try:
                data = json.loads(value)
            except (ValueError, TypeError):
                return value
            for key in self.json_path:
                if not isinstance(data, dict) or key not in data:
                    return value
                data = data[key]
            return data
        return value

    def get_db_converters(self, connection):
        converters = super().get_db_converters(connection)
        converters += [self.convert_json_value]
        return converters


class BooleanField(JSONFieldMixin, fields.BooleanField):
    def __init__(self, *args, **kwargs):
        super(BooleanField, self).__init__(*args, **kwargs)
        self.blank = False


class CharField(JSONFieldMixin, fields.CharField):
    pass


class DateField(JSONFieldMixin, fields.DateField):
    def to_json(self, value):
        if value:
            assert isinstance(value, (datetime, date))
            return value.strftime("%Y-%m-%d")

    def from_json(self, value):
        if value is not None:
            return dateparse.parse_date(value)


class DateTimeField(JSONFieldMixin, fields.DateTimeField):
    def to_json(self, value):
        if value:
            if not timezone.is_aware(value):
                value = timezone.make_aware(value)
            return value.isoformat()

    def from_json(self, value):
        if value:
            return dateparse.parse_datetime(value)


class DecimalField(JSONFieldMixin, fields.DecimalField):
    def to_json(self, value):
        if value is not None:
            return str(value)

    def from_json(self, value):
        if value is not None:
            return Decimal(value)


class EmailField(JSONFieldMixin, fields.EmailField):
    pass


class FloatField(JSONFieldMixin, fields.FloatField):
    pass


class IntegerField(JSONFieldMixin, fields.IntegerField):
    pass


class BigIntegerField(JSONFieldMixin, fields.BigIntegerField):
    pass


class SmallIntegerField(JSONFieldMixin, fields.SmallIntegerField):
    pass


class PositiveIntegerField(JSONFieldMixin, fields.PositiveIntegerField):
    pass


class PositiveSmallIntegerField(JSONFieldMixin, fields.PositiveSmallIntegerField):
    pass


class PositiveBigIntegerField(JSONFieldMixin, fields.PositiveBigIntegerField):
    pass


class IPAddressField(JSONFieldMixin, fields.IPAddressField):
    pass


class GenericIPAddressField(JSONFieldMixin, fields.GenericIPAddressField):
    pass


class NullBooleanField(JSONFieldMixin, fields.NullBooleanField):
    pass


class TextField(JSONFieldMixin, fields.TextField):
    pass


class TimeField(JSONFieldMixin, fields.TimeField):
    def to_json(self, value):
        if value:
            if not timezone.is_aware(value):
                value = timezone.make_aware(value)
            return value.isoformat()

    def from_json(self, value):
        if value:
            return dateparse.parse_time(value)


class URLField(JSONFieldMixin, fields.URLField):
    pass


class SlugField(JSONFieldMixin, fields.SlugField):
    pass


class FilePathField(JSONFieldMixin, fields.FilePathField):
    pass


class UUIDField(JSONFieldMixin, fields.UUIDField):
    def to_json(self, value):
        if value is not None:
            return str(value)

    def from_json(self, value):
        if value is None or isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class DurationField(JSONFieldMixin, fields.DurationField):
    def to_json(self, value):
        if value is not None:
            return duration_iso_string(value)

    def from_json(self, value):
        if value is None or isinstance(value, timedelta):
            return value
        return dateparse.parse_duration(value)


class BinaryField(JSONFieldMixin, fields.BinaryField):
    def __init__(self, *args, **kwargs):
        # A JSON Store field is edited like any other; allow it in forms.
        kwargs.setdefault("editable", True)
        super().__init__(*args, **kwargs)

    def to_json(self, value):
        # bytes aren't JSON-native -- store base64.
        if value is not None:
            return base64.b64encode(bytes(value)).decode("ascii")

    def from_json(self, value):
        if value is None or isinstance(value, bytes):
            return value
        if isinstance(value, (bytearray, memoryview)):
            return bytes(value)
        return base64.b64decode(value)


class JSONField(JSONFieldMixin, BaseJSONField):
    pass


class ForeignKey(JSONFieldMixin, BaseForeignKey):
    """A ForeignKey whose value is kept inside a JSONField.

    The related object's primary key is stored in the JSON blob under
    ``<name>_id`` (the usual Django attname); ``instance.<name>`` returns
    the related object (loaded lazily and cached) and ``instance.<name>_id``
    the raw pk::

        class Book(models.Model):
            data = models.JSONField(default=dict)
            author = jsonstore.ForeignKey(Author, null=True, blank=True)

        book.author = some_author     # data == {"author_id": some_author.pk}
        book.author                   # -> <Author: ...>

    ``formfield()`` yields a ``ModelChoiceField``, so it works in Viewflow /
    Django forms out of the box.

    There is no database-level foreign-key constraint (the value lives in a
    JSON document), so ``on_delete`` has no effect and no reverse accessor
    is created on the target model. Query it through the JSON key, e.g.
    ``Book.objects.filter(data__author_id=author.pk)``; ORM joins such as
    ``filter(author__name=...)`` and ``select_related`` are not available.
    """

    def __init__(self, to, on_delete=None, **kwargs):
        # The value lives in a JSON document, so there is no DB constraint
        # and on_delete is irrelevant; keep the argument for API familiarity.
        super().__init__(to, on_delete or DO_NOTHING, **kwargs)

    def to_json(self, value):
        # Store a JSON-native primary key: int/str pass through, anything
        # else (a UUID pk, most notably) is stored as its string form so the
        # default JSONField encoder can serialize it.
        if value is None or isinstance(value, (int, str)):
            return value
        return str(value)

    def from_json(self, value):
        # Coerce the stored pk back to the target model's pk python type
        # (e.g. str -> UUID), so instance.<name>_id has the expected type.
        if value is None:
            return None
        return self.related_model._meta.pk.to_python(value)

    def contribute_to_class(self, cls, name, private_only=False, **kwargs):
        # JSONFieldMixin installs the id descriptor at attname (``<name>_id``)
        # and registers the field as private/non-concrete (no column).
        super().contribute_to_class(cls, name, private_only=private_only)
        # Expose the related object under the plain field name.
        setattr(cls, self.name, ForeignObjectDescriptor(self))
        # Resolve a string ``"app.Model"`` reference once the apps are ready.
        if isinstance(self.remote_field.model, str):

            def resolve_related(model, related, field):
                field.remote_field.model = related

            lazy_related_operation(
                resolve_related, cls, self.remote_field.model, field=self
            )


class OneToOneField(ForeignKey):
    """A OneToOne relation stored in a JSONField.

    Forward access is identical to :class:`ForeignKey`: the related pk is kept
    under ``<name>_id``, ``instance.<name>`` loads the object lazily, and
    ``formfield()`` is a ``ModelChoiceField``. Being document-based there is no
    database ``UNIQUE`` constraint or reverse accessor, so the one-to-one
    nature is a modelling convention rather than an enforced invariant (it is
    stored exactly like a ``ForeignKey``).
    """


class ManyRelatedJSONManager(object):
    """Manager returned by a jsonstore :class:`ManyToManyField`.

    The related primary keys live in a list inside the JSON blob. The manager
    mimics the common Django related-manager API (``all``/``add``/``remove``/
    ``set``/``clear``/``count``) but, like every JSON Store field, only mutates
    the in-memory document -- call ``instance.save()`` to persist.
    """

    def __init__(self, field, instance):
        self.field = field
        self.instance = instance

    def _prep_pk(self, obj):
        pk = obj.pk if hasattr(obj, "pk") else obj
        # keep JSON-native pks as-is; store anything else (a UUID) as a string
        if pk is None or isinstance(pk, (int, str)):
            return pk
        return str(pk)

    def _get_pks(self):
        data = getattr(self.instance, self.field.json_field_name)
        if not isinstance(data, dict):
            return []
        container, leaf = _json_resolve(data, self.field.json_path)
        if isinstance(container, dict) and isinstance(container.get(leaf), list):
            return list(container[leaf])
        return []

    def _set_pks(self, pks):
        data = getattr(self.instance, self.field.json_field_name)
        if not isinstance(data, dict):
            data = {}
        container, leaf = _json_resolve(data, self.field.json_path, create=True)
        if pks:
            container[leaf] = list(pks)
        else:
            container.pop(leaf, None)
        setattr(self.instance, self.field.json_field_name, data)

    def all(self):
        pks = self._get_pks()
        manager = self.field.related_model._base_manager
        return manager.filter(pk__in=pks) if pks else manager.none()

    def set(self, objs):
        self._set_pks([self._prep_pk(obj) for obj in objs])

    def add(self, *objs):
        pks = self._get_pks()
        for obj in objs:
            pk = self._prep_pk(obj)
            if pk not in pks:
                pks.append(pk)
        self._set_pks(pks)

    def remove(self, *objs):
        drop = {self._prep_pk(obj) for obj in objs}
        self._set_pks([pk for pk in self._get_pks() if pk not in drop])

    def clear(self):
        self._set_pks([])

    def count(self):
        return len(self._get_pks())

    def __iter__(self):
        return iter(self.all())

    def __len__(self):
        return self.count()


class ManyRelatedJSONDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        return ManyRelatedJSONManager(self.field, instance)

    def __set__(self, instance, value):
        ManyRelatedJSONManager(self.field, instance).set(value or [])


class ManyToManyField(JSONFieldMixin, BaseManyToManyField):
    """A ManyToMany relation kept as a list of pks inside a JSONField.

    Instead of a join table, the related primary keys are stored in a list in
    the JSON blob under the field name. ``instance.<name>`` returns a manager
    with the familiar ``all``/``add``/``remove``/``set``/``clear``/``count``
    API::

        class Post(models.Model):
            data = models.JSONField(default=dict)
            tags = jsonstore.ManyToManyField(Tag)

        post.tags.set([tag1, tag2])   # data == {"tags": [tag1.pk, tag2.pk]}
        post.tags.add(tag3)
        list(post.tags.all())         # [<Tag: ...>, ...]

    ``formfield()`` yields a ``ModelMultipleChoiceField``, so it works in
    Viewflow / Django forms and the admin; when saved through a form the
    selection is persisted for you.

    Like the other JSON Store fields the manager only mutates the in-memory
    document -- call ``instance.save()`` after ``add``/``remove``/``set`` to
    persist. There is no join table, ``through`` model or reverse accessor,
    and ``all()`` returns a plain ``filter(pk__in=...)`` queryset (database
    order, not insertion order). Membership queries go through the JSON key
    and depend on the database's JSON support, e.g. on PostgreSQL
    ``Post.objects.filter(data__tags__contains=[tag.pk])``.
    """

    def __init__(self, to, **kwargs):
        kwargs.setdefault("blank", True)
        super().__init__(to, **kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        # JSONFieldMixin registers the field private/non-concrete (no join
        # table); expose the manager under the field name.
        super().contribute_to_class(cls, name)
        setattr(cls, self.name, ManyRelatedJSONDescriptor(self))
        if isinstance(self.remote_field.model, str):

            def resolve_related(model, related, field):
                field.remote_field.model = related

            lazy_related_operation(
                resolve_related, cls, self.remote_field.model, field=self
            )

    def check(self, **kwargs):
        # Skip the join-table/through-model checks of a real ManyToManyField;
        # this field has none of that machinery.
        return fields.Field.check(self, **kwargs)

    def save_form_data(self, instance, data):
        # Called by ModelForm.save_m2m() after the instance is already saved;
        # the pks live in the JSON column, so persist the change ourselves.
        getattr(instance, self.name).set(data)
        if instance.pk is not None:
            instance.save(update_fields=[self.json_field_name])

    def value_from_object(self, obj):
        return list(getattr(obj, self.name).all())


class EmbeddedFieldDescriptor(object):
    """Access one field of an :class:`EmbeddedModel`, backed by its ``_store``
    dict (which is the sub-document living inside the parent's JSONField)."""

    def __init__(self, field):
        self.field = field

    def __get__(self, instance, cls=None):
        if instance is None:
            return self.field
        container, leaf = _json_resolve(instance._store, self.field.json_path)
        if isinstance(container, dict) and leaf in container:
            value = container.get(leaf)
            if hasattr(self.field, "from_json"):
                value = self.field.from_json(value)
            return value
        if self.field.default is not fields.NOT_PROVIDED:
            return (
                self.field.default()
                if callable(self.field.default)
                else self.field.default
            )
        return None

    def __set__(self, instance, value):
        if hasattr(self.field, "to_json"):
            value = self.field.to_json(value)
        container, leaf = _json_resolve(
            instance._store, self.field.json_path, create=True
        )
        if (value is None or value == "") and self.field.blank and not self.field.null:
            container.pop(leaf, None)
        else:
            container[leaf] = value


class EmbeddedModelBase(type):
    """Metaclass collecting the JSON Store fields declared on an
    :class:`EmbeddedModel` and exposing them through descriptors."""

    def __new__(mcs, name, bases, namespace):
        declared = {}
        for base in bases:
            declared.update(getattr(base, "_fields", {}))
        for attr, value in list(namespace.items()):
            if isinstance(value, JSONFieldMixin):
                value.set_attributes_from_name(attr)
                declared[attr] = value
                namespace[attr] = EmbeddedFieldDescriptor(value)
        namespace["_fields"] = declared
        return super().__new__(mcs, name, bases, namespace)


class EmbeddedModel(metaclass=EmbeddedModelBase):
    """A schema-only "virtual model" stored as a nested JSON document.

    Declare typed JSON Store fields, then embed an instance in a host model
    with :class:`EmbeddedField`. It has no database table of its own::

        class Money(jsonstore.EmbeddedModel):
            amount = jsonstore.IntegerField()
            currency = jsonstore.CharField(max_length=3)

        class Product(models.Model):
            data = models.JSONField(default=dict)
            price = jsonstore.EmbeddedField(Money)

        product.price = Money(amount=100, currency="USD")
        product.data          # {"price": {"amount": 100, "currency": "USD"}}
        product.price.amount  # 100

    Reading ``product.price`` returns an instance bound to the stored
    sub-document, so ``product.price.amount = 120`` is persisted by the next
    ``product.save()`` -- like every other JSON Store field.
    """

    def __init__(self, **kwargs):
        self.__dict__["_store"] = {}
        unknown = set(kwargs) - set(self._fields)
        if unknown:
            raise TypeError(
                "%s got unexpected field(s): %s"
                % (type(self).__name__, ", ".join(sorted(unknown)))
            )
        for name, value in kwargs.items():
            setattr(self, name, value)

    @classmethod
    def from_dict(cls, store):
        """Wrap an existing sub-document dict *by reference* (write-through)."""
        obj = cls.__new__(cls)
        obj.__dict__["_store"] = store if store is not None else {}
        return obj

    def to_dict(self):
        return self._store

    def __eq__(self, other):
        return isinstance(other, EmbeddedModel) and self._store == other._store

    def __hash__(self):
        return None  # mutable, like dict

    def __repr__(self):
        return "<%s %r>" % (type(self).__name__, self._store)


class EmbeddedField(JSONFieldMixin, BaseJSONField):
    """Store an :class:`EmbeddedModel` instance as a nested JSON document.

    The sub-document lives under the field's key (customisable with
    ``json_key``); ``instance.<name>`` returns the embedded model bound to it
    (so in-place edits are saved), and assigning ``None`` clears it. Like the
    relation fields it is virtual -- no column or migration. Query the nested
    values through the raw JSON key, e.g.
    ``Product.objects.filter(data__price__amount=100)``.
    """

    def __init__(self, embedded_model, **kwargs):
        if not (
            isinstance(embedded_model, type)
            and issubclass(embedded_model, EmbeddedModel)
        ):
            raise TypeError("EmbeddedField expects an EmbeddedModel subclass")
        self.embedded_model = embedded_model
        super().__init__(**kwargs)

    def to_json(self, value):
        if value is None:
            return None
        if isinstance(value, EmbeddedModel):
            return copy.deepcopy(value.to_dict())
        if isinstance(value, dict):
            return copy.deepcopy(value)
        raise TypeError(
            "%s expects a %s instance or dict, got %s"
            % (self.name, self.embedded_model.__name__, type(value).__name__)
        )

    def from_json(self, value):
        if value is None:
            return None
        if isinstance(value, EmbeddedModel):
            return value
        return self.embedded_model.from_dict(value)


class EmbeddedList(collections.abc.MutableSequence):
    """A list of :class:`EmbeddedModel` instances stored as an array of JSON
    documents inside the parent's JSONField.

    Behaves like a mutable list -- indexing, iteration, ``len``, ``append``,
    ``insert``, ``del`` -- of embedded instances. Elements are bound to their
    stored document, so ``obj.items[0].qty = 5`` is persisted by the next
    ``obj.save()``. Like every JSON Store field it only mutates the in-memory
    document.
    """

    def __init__(self, field, instance):
        self.field = field
        self.instance = instance

    def _coerce(self, value):
        if isinstance(value, EmbeddedModel):
            return copy.deepcopy(value.to_dict())
        if isinstance(value, dict):
            return copy.deepcopy(value)
        raise TypeError(
            "%s expects %s instances or dicts, got %s"
            % (
                self.field.name,
                self.field.embedded_model.__name__,
                type(value).__name__,
            )
        )

    def _get_list(self):
        data = getattr(self.instance, self.field.json_field_name)
        if not isinstance(data, dict):
            return []
        container, leaf = _json_resolve(data, self.field.json_path)
        if isinstance(container, dict) and isinstance(container.get(leaf), list):
            return container[leaf]
        return []

    def _ensure_list(self):
        data = getattr(self.instance, self.field.json_field_name)
        if not isinstance(data, dict):
            data = {}
        container, leaf = _json_resolve(data, self.field.json_path, create=True)
        if not isinstance(container.get(leaf), list):
            container[leaf] = []
        setattr(self.instance, self.field.json_field_name, data)
        return container[leaf]

    def _replace(self, items):
        stored = [self._coerce(item) for item in items]
        if stored:
            self._ensure_list()[:] = stored
        else:
            # drop the (possibly nested) key entirely when empty
            data = getattr(self.instance, self.field.json_field_name)
            if isinstance(data, dict):
                container, leaf = _json_resolve(data, self.field.json_path)
                if isinstance(container, dict):
                    container.pop(leaf, None)

    def __getitem__(self, index):
        stored = self._get_list()
        if isinstance(index, slice):
            return [self.field.embedded_model.from_dict(doc) for doc in stored[index]]
        # bound by reference -> in-place edits on the element persist
        return self.field.embedded_model.from_dict(stored[index])

    def __setitem__(self, index, value):
        stored = self._ensure_list()
        if isinstance(index, slice):
            stored[index] = [self._coerce(item) for item in value]
        else:
            stored[index] = self._coerce(value)

    def __delitem__(self, index):
        del self._ensure_list()[index]

    def __len__(self):
        return len(self._get_list())

    def insert(self, index, value):
        self._ensure_list().insert(index, self._coerce(value))

    def __eq__(self, other):
        return list(self) == list(other)

    def __repr__(self):
        return "<EmbeddedList %r>" % (list(self),)


class EmbeddedListDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance, cls=None):
        if instance is None:
            return self
        return EmbeddedList(self.field, instance)

    def __set__(self, instance, value):
        EmbeddedList(self.field, instance)._replace(value or [])


class EmbeddedListField(JSONFieldMixin, BaseJSONField):
    """Store a list of :class:`EmbeddedModel` instances as an array of JSON
    documents -- the embedded-document analogue of :class:`ManyToManyField`.

    ::

        class Order(models.Model):
            data = models.JSONField(default=dict)
            lines = jsonstore.EmbeddedListField(LineItem)

        order.lines = [LineItem(sku="a", qty=1), LineItem(sku="b", qty=2)]
        order.lines.append(LineItem(sku="c", qty=3))
        order.lines[0].qty = 5          # in-place edit, persisted on save()
        order.data                      # {"lines": [{...}, {...}, {...}]}

    ``instance.<name>`` is a mutable, list-like accessor of embedded
    instances. Like the other JSON Store fields it mutates the in-memory
    document (call ``save()`` to persist), and accepts ``json_key`` /
    ``json_field_name`` to place the array anywhere in the parent.
    """

    def __init__(self, embedded_model, **kwargs):
        if not (
            isinstance(embedded_model, type)
            and issubclass(embedded_model, EmbeddedModel)
        ):
            raise TypeError("EmbeddedListField expects an EmbeddedModel subclass")
        self.embedded_model = embedded_model
        kwargs.setdefault("blank", True)
        super().__init__(**kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name)
        setattr(cls, self.name, EmbeddedListDescriptor(self))
