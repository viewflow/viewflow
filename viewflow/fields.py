import six
from six import add_metaclass
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
    if app_config.module.__package__ is not None:
        # python 3?
        subpath = app_config.module.__package__+'.flows'
    else:
        # python 2?
        subpath = app_config.module.__name__+'.flows'

    flow_cls = import_by_path('{}{}'.format(subpath, flow_path))
    return getattr(flow_cls, task_name)


def get_task_ref(flow_task):
    module = flow_task.flow_cls.__module__
    app_config = apps.get_containing_app_config(module)
    if app_config.module.__package__ is not None:
        # python 3?
        subpath = module.lstrip(app_config.module.__package__+'.flows.')
    else:
        # python 2?
        subpath = module.lstrip(app_config.module.__name__+'.flows.')

    return "{}/{}.{}.{}".format(app_config.label, subpath, flow_task.flow_cls.__name__, flow_task.name)


@add_metaclass(models.SubfieldBase)
class FlowReferenceField(models.CharField):
    description = """Flow class reference field,
    stores flow as app_label/flows.FlowName> to
    avoid possible collisions with app name changes"""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 250)
        super(FlowReferenceField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, six.string_types) and value:
            app_label, flow_path = value.split('/')
            app_config = apps.get_app_config(app_label)

            if app_config.module.__package__ is not None:
                # python 3?
                subpath = app_config.module.__package__+'.flows'
            else:
                # python 2?
                subpath = app_config.module.__name__+'.flows'

            return import_by_path('{}.{}'.format(subpath, flow_path))
        return value

    def get_prep_value(self, value):
        if not isinstance(value, type):
            # HACK: Django calls callable due query parameter
            # preparation. So here we can get Flow instance,
            # even if we pass Flow class to query.
            value = value.__class__

        module = "{}.{}".format(value.__module__, value.__name__)
        app_config = apps.get_containing_app_config(module)
        if app_config.module.__package__ is not None:
            # python 3?
            subpath = module.lstrip(app_config.module.__package__+'.flows.')
        else:
            # python 2?
            subpath = module.lstrip(app_config.module.__name__+'.flows.')
        return "{}/{}".format(app_config.label, subpath)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)


@add_metaclass(models.SubfieldBase)
class TaskReferenceField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 150)
        super(TaskReferenceField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, six.string_types) and value:
            return import_task_by_ref(value)
        return value

    def get_prep_value(self, value):
        if not isinstance(value, six.string_types):
            return get_task_ref(value)
        return super(TaskReferenceField, self).get_prep_value(value)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)


@add_metaclass(models.SubfieldBase)
class TokenField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 150)
        if 'default' in kwargs:
            default = kwargs['default']
            if isinstance(default, six.string_types):
                kwargs['default'] = Token(default)
        super(TokenField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if isinstance(value, six.string_types) and value:
            return Token(value)
        return value

    def get_prep_value(self, value):
        if not isinstance(value, six.string_types):
            return value.token
        return super(TokenField, self).get_prep_value(value)
