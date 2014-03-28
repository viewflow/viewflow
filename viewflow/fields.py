from django.apps import apps
from django.db import models
from django.db.models.fields import NOT_PROVIDED
from django.utils.module_loading import import_by_path


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


class TaskReferenceField(models.CharField, metaclass=models.SubfieldBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 150)
        super(TaskReferenceField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, str) and value:
            app_label, flow_path = value.split('/')
            flow_path, task_name = flow_path.rsplit('.', 1)
            app_config = apps.get_app_config(app_label)
            flow_cls = import_by_path('{}.{}'.format(app_config.module.__package__, flow_path))
            return getattr(flow_cls, task_name)
        return value

    def get_prep_value(self, value):
        if not isinstance(value, str):
            module = value.flow_cls.__module__
            app_config = apps.get_containing_app_config(module)
            subpath = module.lstrip(app_config.module.__package__+'.')

            return "{}/{}.{}.{}".format(app_config.label, subpath, value.flow_cls.__name__, value.name)
        return super(TaskReferenceField, self).get_prep_value(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)
