from functools import lru_cache

from django.db import models
from django.utils.module_loading import import_string

from viewflow.utils import get_app_package, get_containing_app_data
from viewflow.workflow.exceptions import FlowRuntimeError
from viewflow.workflow.token import Token


@lru_cache(maxsize=None)
def import_flow_by_ref(flow_strref):
    """Return flow class by flow string reference."""
    app_label, flow_path = flow_strref.split("/")
    # TODO Raise if imported class is not Flow
    return import_string("{}.{}".format(get_app_package(app_label), flow_path))


@lru_cache(maxsize=None)
def get_flow_ref(flow_class):
    """Convert flow class to string reference."""
    module = "{}.{}".format(flow_class.__module__, flow_class.__name__)
    app_label, app_package = get_containing_app_data(module)
    if app_label is None:
        raise FlowRuntimeError(
            "No application found for {}. Check your INSTALLED_APPS setting".format(
                module
            )
        )

    subpath = module[len(app_package) + 1 :]
    return "{}/{}".format(app_label, subpath)


@lru_cache(maxsize=None)
def import_task_by_ref(task_strref):
    """Return flow task by reference like `app_label/path.to.Flowclass.task_name`."""
    app_label, flow_path = task_strref.split("/")
    flow_path, task_name = flow_path.rsplit(".", 1)
    flow_class = import_string("{}.{}".format(get_app_package(app_label), flow_path))
    # TODO Raise if imported class is not Node
    return flow_class.instance.node(task_name)


@lru_cache(maxsize=None)
def get_task_ref(flow_task):
    """Convert task to the string reference suitable to store in the db."""
    module = flow_task.flow_class.__module__
    app_label, app_package = get_containing_app_data(module)
    if app_label is None:
        raise FlowRuntimeError(
            "No application found for {}. Check your INSTALLED_APPS setting".format(
                module
            )
        )

    subpath = module[len(app_package) + 1 :]

    return "{}/{}.{}.{}".format(
        app_label, subpath, flow_task.flow_class.__name__, flow_task.name
    )


class FlowReferenceField(models.CharField):
    description = """Flow class reference field,
    stores flow as app_label/flows.FlowName> to
    avoid possible collisions with app name changes"""

    def __init__(self, *args, **kwargs):  # noqa D1o2
        kwargs.setdefault("max_length", 250)
        super(FlowReferenceField, self).__init__(*args, **kwargs)

    def to_python(self, value):  # noqa D102
        if value:
            return import_flow_by_ref(value)
        return value

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return import_flow_by_ref(value)
        except LookupError:
            return None

    def get_prep_value(self, value):  # noqa D1o2
        if value and not isinstance(value, str):
            return get_flow_ref(value)
        return value

    def value_to_string(self, obj):  # noqa D1o2
        value = super(FlowReferenceField, self).value_from_object(obj)
        return self.get_prep_value(value)


class TaskReferenceField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 255)
        super(TaskReferenceField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value:
            return import_task_by_ref(value)  # TODO Raise  ValidationError
        return value

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return import_task_by_ref(value)

    def get_prep_value(self, value):  # noqa D102
        if value and not isinstance(value, str):
            return get_task_ref(value)
        return value

    def value_to_string(self, obj):  # noqa D102
        value = super(TaskReferenceField, self).value_from_object(obj)
        return self.get_prep_value(value)


class TokenField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 150)
        super(TokenField, self).__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        return Token(value)

    def to_python(self, value):
        return Token(value)

    def get_prep_value(self, value):
        return value.token
