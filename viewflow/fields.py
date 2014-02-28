from django.apps import apps
from django.db import models
from django.utils.module_loading import import_by_path

from viewflow.flow import _Node


class FlowReferenceField(models.CharField, metaclass=models.SubfieldBase):
    description = """Flow class reference field,
    stores flow as app_label/flows.FlowName> to
    avoid possible collisions with app name changes"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 250)
        super(FlowReferenceField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, str) and value:
            app_label, flow_path = value.split('/')
            app_config = apps.get_app_config(app_label)
            return import_by_path('{}.{}'.format(app_config.module.__package__, flow_path))
        return value

    def get_prep_value(self, value):
        if not isinstance(value, type):
            # HACK: Django calls callable due query parameter
            # preparation. So here we can get Flow instance,
            # even if we pass Flow class to query.
            value = value.__class__

        module = "{}.{}".format(value.__module__, value.__name__)
        app_config = apps.get_containing_app_config(module)
        subpath = module.lstrip(app_config.module.__package__+'.')
        return "{}/{}".format(app_config.label, subpath)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)


class TaskDescriptor(object):
    def __init__(self, field):
        self.field = field

    def __get__(self, instance=None, owner=None):
        if instance is None:
            raise AttributeError(
                "The '%s' attribute can only be accessed from %s instances."
                % (self.field.name, owner.__name__))

        task = instance.__dict__[self.field.name]

        if not isinstance(task, _Node):
            flow_cls = self._get_instance_value(instance, self.field.flow_cls_ref)
            task = getattr(flow_cls, task)
        return task

    def __set__(self, instance, value):
        if isinstance(value, _Node):
            value = value.name

        instance.__dict__[self.field.name] = value

    def _get_instance_value(self, instance, key):
        if '__' in key:
            field, _, subfield_key = key.partition('__')
            instance = getattr(instance, field)
            if not instance:
                raise ValueError('{} have no {} field'.format(instance, field))
            return self._get_instance_value(instance, subfield_key)
        return getattr(instance, key)


class TaskReferenceField(models.CharField):
    def __init__(self, flow_cls_ref=None, *args, **kwargs):
        kwargs.setdefault('max_length', 150)

        if flow_cls_ref is None:
            raise ValueError('Reference to Flow class field not provided')
        self.flow_cls_ref = flow_cls_ref

        super(TaskReferenceField, self).__init__(*args, **kwargs)

    def contribute_to_class(self, cls, name):
        super(TaskReferenceField, self).contribute_to_class(cls, name)
        setattr(cls, self.name, TaskDescriptor(self))

    def deconstruct(self):
        name, path, args, kwargs = super(TaskReferenceField, self).deconstruct()
        kwargs['flow_cls_ref'] = self.flow_cls_ref
        return name, path, args, kwargs

    def get_default(self):
        if isinstance(self.default, _Node):
            return self.default.name
        return super(TaskReferenceField, self).get_default()

    def get_prep_value(self, value):
        if isinstance(value, _Node):
            return value.name
        return super(TaskReferenceField, self).get_prep_value(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)
