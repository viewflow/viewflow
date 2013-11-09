from django.db import models
from django.utils.module_loading import import_by_path


class ClassReferenceField(models.CharField):
    description = "Python class reference"

    def __init__(self, *args, **kwargs):
         kwargs.setdefault('max_length', 250)
         super(ClassReferenceField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        return import_by_path(value)

    def get_prep_value(self, value):
        return "{}.{}".format(value.__module__, value.__name__)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_prep_value(value)
