from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q
from django.db.models.constants import LOOKUP_SEP
from django.utils.text import smart_split, unescape_string_literal


def lookup_spawns_duplicates(opts, lookup_path):
    """
    from django.contrib.admin.utils import lookup_spawns_duplicates

    Return True if the given lookup path spawns duplicates.
    """
    lookup_fields = lookup_path.split(LOOKUP_SEP)
    # Go through the fields (following all relations) and look for an m2m.
    for field_name in lookup_fields:
        if field_name == 'pk':
            field_name = opts.pk.name
        try:
            field = opts.get_field(field_name)
        except FieldDoesNotExist:
            # Ignore query lookups.
            continue
        else:
            if hasattr(field, 'path_infos'):
                # This field is a relation; update opts to follow the relation.
                path_info = field.path_infos
                opts = path_info[-1].to_opts
                if any(path.m2m for path in path_info):
                    # This field is a m2m relation so duplicates must be
                    # handled.
                    return True
    return False


def construct_search(opts, field_name):
    """
    Implementation similar to django.contrib.admin.options.ModelAdmin.get_search_results
    """
    if field_name.startswith("^"):
        return "%s__istartswith" % field_name[1:]
    elif field_name.startswith("="):
        return "%s__iexact" % field_name[1:]
    elif field_name.startswith("@"):
        return "%s__search" % field_name[1:]

    # Use field_name if it includes a lookup.
    lookup_fields = field_name.split(LOOKUP_SEP)

    # Go through the fields, following all relations.
    prev_field = None
    for path_part in lookup_fields:
        if path_part == "pk":
            path_part = opts.pk.name
        try:
            field = opts.get_field(path_part)
        except FieldDoesNotExist:
            # Use valid query lookups.
            if prev_field and prev_field.get_lookup(path_part):
                return field_name
        else:
            prev_field = field
            if hasattr(field, "path_infos"):
                # Update opts to follow the relation.
                opts = field.path_infos[-1].to_opts

    # Otherwise, use the field with icontains.
    return "%s__icontains" % field_name


def get_search_results(queryset, search_fields, search_term):
    """
    Implementation similar to django.contrib.admin.options.ModelAdmin.get_search_results
    """
    opts = queryset.model._meta

    orm_lookups = [
        construct_search(opts, str(search_field)) for search_field in search_fields
    ]

    for bit in smart_split(search_term):
        if bit.startswith(('"', "'")) and bit[0] == bit[-1]:
            bit = unescape_string_literal(bit)
        or_queries = Q(
            *((orm_lookup, bit) for orm_lookup in orm_lookups),
            _connector=Q.OR,
        )
        queryset = queryset.filter(or_queries)

    may_have_duplicates = any(
        lookup_spawns_duplicates(opts, search_spec)
        for search_spec in orm_lookups
    )

    if may_have_duplicates:
        queryset = queryset.distinct()

    return queryset


class SearchableViewMixin(object):
    """
    The mixin for LitView to enable search capabilities
    """
    search_fields = None

    def search_enabled(self):
        return self.search_fields is not None

    def get_search_term(self):
        return self.request.GET.get('_search')

    def get_queryset(self):
        queryset = super().get_queryset()
        search_term = self.get_search_term()
        if self.search_enabled is not None and search_term is not None:
            queryset = get_search_results(queryset, self.search_fields, search_term)
        return queryset
