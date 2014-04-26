from django.apps import apps
from django.db import models
from django.utils.module_loading import import_by_path
from viewflow.token import Token


def import_task_by_ref(task_strref):
    """
    Return flow task by reference like `app_label/path.to.Flowcls.task_name`
    """
    app_label, flow_path = task_strref.split('/')
    flow_path, task_name = flow_path.rsplit('.', 1)
    app_config = apps.get_app_config(app_label)
    flow_cls = import_by_path('{}.{}'.format(app_config.module.__package__, flow_path))
    return getattr(flow_cls, task_name)


def get_task_ref(flow_task):
    module = flow_task.flow_cls.__module__
    app_config = apps.get_containing_app_config(module)
    subpath = module.lstrip(app_config.module.__package__+'.')

    return "{}/{}.{}.{}".format(app_config.label, subpath, flow_task.flow_cls.__name__, flow_task.name)


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
            return import_task_by_ref(value)
        return value

    def get_prep_value(self, value):
        if not isinstance(value, str):
            return get_task_ref(value)
        return super(TaskReferenceField, self).get_prep_value(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)


class TokenField(models.CharField, metaclass=models.SubfieldBase):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 150)
        if 'default' in kwargs:
            default = kwargs['default']
            if isinstance(default, str):
                kwargs['default'] = Token(default)
        super(TokenField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, str) and value:
            return Token(value)
        return value

    def get_prep_value(self, value):
        if not isinstance(value, str):
            return value.token
        return super(TokenField, self).get_prep_value(value)
