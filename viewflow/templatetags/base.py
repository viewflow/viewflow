from __future__ import unicode_literals

from django.db import models
from django.db.models.fields.related import ForeignObjectRel
from django.contrib.auth import get_permission_codename
from django.urls import reverse, NoReverseMatch



def get_model_display_data(root_instance, user):
    """
    Return structure with model fields and related from same app.

    Example:

        [(Title, [(Field Title, Value), ... ]), ...]

    """
    result = []
    new_objects = [(root_instance._meta.verbose_name.title(), root_instance)]

    processed_models, processed_objects = [], []

    def expand_required(instance):
        if instance in processed_objects:
            return False
        if instance.__class__ in processed_models:
            return False
        return (root_instance._meta.app_label == instance._meta.app_label)

    while new_objects:
        root_title, root = new_objects.pop(0)
        root_admin_url = None
        children = []

        processed_objects.append(root)
        processed_models.append(root.__class__)

        # objects fields
        for field in root._meta.fields:
            if isinstance(field, models.AutoField):
                continue
            elif field.auto_created:
                continue
            elif isinstance(field, models.ForeignKey) and not field.auto_created:
                related_id = getattr(root, field.get_attname())
                if related_id is not None:
                    related = getattr(root, field.name)
                    if expand_required(related):
                        if root_instance._meta.app_label == related._meta.app_label:
                            new_objects.append((field.verbose_name.title(), related))
                        else:
                            value = getattr(root, field.name)
                            if value is not None:
                                children.append((field.verbose_name.title(), value))
            else:
                choice_display_attr = "get_{}_display".format(field.get_attname())
                if hasattr(root, choice_display_attr):
                    value = getattr(root, choice_display_attr)()
                else:
                    value = getattr(root, field.get_attname())

                if value is not None:
                    children.append((field.verbose_name.title(), value))

        # backward relations
        backward_relations = [
            field for field in root._meta.get_fields()
            if isinstance(field, ForeignObjectRel)
        ]
        for relation in backward_relations:
            if not isinstance(relation.field, models.OneToOneField):
                for related in getattr(root, relation.get_accessor_name()).all():
                    if expand_required(related):
                        new_objects.append((related._meta.verbose_name.title(), related))

        # if any suitable for display children found
        if children:
            change_perm = get_permission_codename('change', root._meta)
            if user.has_perm("%s.%s" % (root._meta.app_label, change_perm)):
                admin_url_name = "admin:{}_{}_change".format(root._meta.app_label, root._meta.model_name)
                try:
                    root_admin_url = reverse(admin_url_name, args=(root.pk,))
                except NoReverseMatch:
                    pass

            result.append((root_title, children, root_admin_url))

    return result
