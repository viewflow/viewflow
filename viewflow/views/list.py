# Copyright (c) 2017-2020, Mikhail Podgurskiy
# All Rights Reserved.

# This work is dual-licensed under AGPL defined in file 'LICENSE' with
# LICENSE_EXCEPTION and the Commercial license defined in file 'COMM_LICENSE',
# which is part of this source code package.

import datetime
import decimal
from functools import lru_cache

from django.contrib.auth.decorators import login_required
from django.core.exceptions import FieldDoesNotExist, PermissionDenied
from django.db import models
from django.forms.utils import pretty_name
from django.utils import formats, timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.views import generic

from viewflow.utils import Icon, has_object_perm, viewprop
from .filters import FilterableViewMixin
from .search import SearchableViewMixin


def _get_method_attr(data_source, method_name, attr_name, default=None):
    attr = getattr(data_source, method_name)
    try:
        return getattr(attr, attr_name)
    except AttributeError:
        if isinstance(attr, property) and hasattr(attr, "fget"):
            return getattr(attr.fget, attr_name, default)
    return default


class BaseColumn(object):
    def __init__(self, attr_name):
        self.attr_name = attr_name

    def get_value(self, obj):
        raise NotImplementedError("subclasses must implement this method.")

    def header(self):
        raise NotImplementedError("subclasses must implement this method")

    def column_type(self):
        raise NotImplementedError("subclasses must implement this method")

    def orderby(self):
        raise NotImplementedError("subclasses must implement this method")

    def format_value(self, obj, value):
        if value is None:
            return ""
        elif isinstance(value, datetime.datetime):
            return formats.localize(timezone.template_localtime(value))
        elif isinstance(value, (datetime.date, datetime.time)):
            return formats.localize(value)
        elif isinstance(value, (int, float, decimal.Decimal)):
            return formats.number_format(value)
        elif isinstance(value, (list, tuple)):
            return ", ".join(force_str(v) for v in value)
        else:
            return force_str(value)


class ModelFieldColumn(BaseColumn):
    """
    Retrieve a field value from a model.

    Field verbose name would be use as a label.
    """

    NUMBER_FIELD_TYPES = (
        models.IntegerField,
        models.DecimalField,
        models.FloatField,
    )

    BOOLEAN_FIELD_TYPES = (models.BooleanField, models.NullBooleanField)

    def __init__(self, model_field):
        super().__init__(model_field.name)
        self.model_field = model_field

    def get_value(self, obj):
        return getattr(obj, self.model_field.name)

    def header(self):
        try:
            return self.model_field.verbose_name.capitalize()
        except AttributeError:
            # field is likely a ForeignObjectRel
            return self.model_field.related_model._meta.verbose_name.capitalize()

    def column_type(self):
        if isinstance(self.model_field, ModelFieldColumn.NUMBER_FIELD_TYPES):
            return "numeric"
        elif isinstance(self.model_field, ModelFieldColumn.BOOLEAN_FIELD_TYPES):
            return "boolean"
        return "text"

    def orderby(self):
        return self.attr_name

    def format_value(self, obj, value):
        if getattr(self.model_field, "flatchoices", None):
            return dict(self.model_field.flatchoices).get(value, "")
        elif isinstance(self.model_field, ModelFieldColumn.BOOLEAN_FIELD_TYPES):
            if value is None:
                return Icon("indeterminate_check_box")
            elif value is True:
                return Icon("check_box")
            else:
                return Icon("check_box_outline_blank")
        else:
            return super().format_value(obj, value)


class DataSourceColumn(BaseColumn):
    """
    Retrieve attribute value from external data source.

    Data source attribute could be a property or callable.
    For a callable, to get the value it would be called with model
    instance.
    """

    def __init__(self, data_source, attr_name, verbose_name=None):
        super().__init__(attr_name)
        self.verbose_name = verbose_name
        self.data_source = data_source

    def _get_attr_boolean(self):
        return _get_method_attr(self.data_source, self.attr_name, "boolean", False)

    def _get_attr_empty_value(self):
        return _get_method_attr(self.data_source, self.attr_name, "empty_value")

    def get_value(self, obj):
        attr = getattr(self.data_source, self.attr_name)
        if callable(attr):
            attr = attr(obj)
        if attr is None:
            attr = self._get_attr_empty_value()
        return attr

    def header(self):
        if self.verbose_name is not None:
            return self.verbose_name
        attr = getattr(self.data_source, self.attr_name)
        if hasattr(attr, "short_description"):
            return attr.short_description
        elif isinstance(attr, property) and hasattr(attr, "fget"):
            if hasattr(attr.fget, "short_description"):
                return attr.fget.short_description
            else:
                return pretty_name(self.attr_name)
        elif callable(attr):
            return "--" if attr.__name__ == "<lambda>" else pretty_name(attr.__name__)
        else:
            return pretty_name(self.attr_name)

    def column_type(self):
        is_boolean = _get_method_attr(self.data_source, self.attr_name, "boolean", None)
        if is_boolean:
            return "boolean"
        return _get_method_attr(self.data_source, self.attr_name, "column_type", "text")

    def orderby(self):
        return _get_method_attr(
            self.data_source, self.attr_name, "orderby_column", None
        )

    def format_value(self, obj, value):
        if self._get_attr_boolean():
            if value is None:
                return Icon("indeterminate_check_box")
            elif value is True:
                return Icon("check_box")
            else:
                return Icon("check_box_outline_blank")
        else:
            return super().format_value(obj, value)


class ObjectAttrColumn(DataSourceColumn):
    """
    Retrieve attribute value from a model instance.

    If object attribute is a callable, to get the value it would be
    called without any arguments.
    """

    def get_value(self, obj):
        attr = getattr(obj, self.attr_name)
        if callable(attr):
            return attr()
        return attr


class OrderableListViewMixin(object):
    ordering = None
    ordering_kwarg = "_orderby"

    def get_ordering(self):
        """Return the field or fields to use for ordering the queryset."""
        ordering = []

        # url query parameter
        if self.ordering_kwarg in self.request.GET:
            params = self.request.GET[self.ordering_kwarg].split(",")
            for param in params:
                _, prefix, param_name = param.rpartition("-")
                column_def = self.list_columns.get(param_name)
                if column_def:
                    column_ordering = column_def.orderby()
                    if column_ordering:
                        if hasattr(column_ordering, "as_sql"):
                            ordering.append(
                                column_ordering.desc()
                                if prefix == "-"
                                else column_ordering.asc()
                            )
                        elif column_ordering.startswith("-") and prefix == "-":
                            ordering.append(column_ordering[1:])
                        else:
                            ordering.append(prefix + column_ordering)
        else:
            # default view ordering
            if isinstance(self.ordering, (list, tuple)):
                ordering.extend(self.ordering)
            elif isinstance(self.ordering, str):
                ordering.append(self.ordering)

            # default queryset order
            if self.queryset is not None:
                ordering.extend(self.queryset.query.order_by)

        return ordering

    @cached_property
    def columns_order(self):
        """Return list of columns used to order the queryset."""
        ordering = {}

        # ordered by the url query
        if self.ordering_kwarg in self.request.GET:
            params = self.request.GET[self.ordering_kwarg].split(",")
            for param in params:
                _, param_prefix, param_name = param.rpartition("-")
                column_def = self.list_columns.get(param_name)
                if column_def:
                    column_ordering = column_def.orderby()
                    if column_ordering is not None and isinstance(column_ordering, str):
                        # TODO support custom OrderBy expressions
                        (
                            _,
                            column_order_prefix,
                            column_orderby,
                        ) = column_ordering.rpartition("-")
                        ordering[column_def] = (
                            "asc" if column_order_prefix == param_prefix else "desc"
                        )
        else:
            # ordered by explicit self.ordering definition or by queryset.order_by
            raw_ordering = []
            if isinstance(self.ordering, (list, tuple)):
                raw_ordering.extend(self.ordering)
            elif isinstance(self.ordering, str):
                raw_ordering.append(self.ordering)
            if self.queryset is not None:
                raw_ordering.extend(self.queryset.query.order_by)

            for param in raw_ordering:
                _, param_prefix, param_name = param.rpartition("-")
                for column_def in self.list_columns.values():
                    if column_def in ordering:  # column order already found
                        continue
                    column_ordering = column_def.orderby()
                    if column_ordering is not None and isinstance(column_ordering, str):
                        # TODO support custom OrderBy expressions
                        (
                            _,
                            column_order_prefix,
                            column_orderby,
                        ) = column_ordering.rpartition("-")
                        if param_name == column_orderby:
                            ordering[column_def] = (
                                "asc" if column_order_prefix == param_prefix else "desc"
                            )

        return ordering


class BulkActionsMixin(object):
    bulk_actions = None

    def get_bulk_actions(self, *actions):
        if self.viewset is not None and hasattr(self.viewset, "get_list_bulk_actions"):
            actions = self.viewset.get_list_bulk_actions(self.request) + actions
        if self.bulk_actions:
            actions = self.bulk_actions + actions
        return actions


class BaseListModelView(generic.ListView):
    viewset = None
    columns = None
    object_link_columns = None
    paginate_by = 25

    page_actions = None

    empty_value_display = ""

    def has_view_permission(self, user, obj=None):
        if self.viewset is not None:
            return self.viewset.has_view_permission(user, obj=obj)
        else:
            return has_object_perm(
                user, "view", self.model, obj=obj
            ) or has_object_perm(user, "change", self.model, obj=obj)

    def get_columns(self):
        if self.columns is None:
            return ["__str__"]
        return self.columns

    @lru_cache(maxsize=None)
    def get_object_link_columns(self):
        if self.object_link_columns is None:
            return self.get_columns()[0]
        return self.object_link_columns

    def get_column_def(self, attr_name):
        opts = self.model._meta

        # object printable string representation
        if attr_name == "__str__":
            return ObjectAttrColumn(
                self.model, attr_name, opts.verbose_name.capitalize()
            )

        # a method from view or viewset
        data_sources = [self, self.viewset] if self.viewset is not None else [self]
        for data_source in data_sources:
            if hasattr(data_source, attr_name):
                return DataSourceColumn(data_source, attr_name)

        # an object field
        try:
            model_field = opts.get_field(attr_name)
        except FieldDoesNotExist:
            pass
        else:
            return ModelFieldColumn(model_field)

        # a method from object
        if hasattr(self.model, attr_name):
            return ObjectAttrColumn(self.model, attr_name)

        raise ValueError("Can't found datasource for {} column".format(attr_name))

    def get_object_url(self, obj):
        if self.viewset is not None and hasattr(self.viewset, "get_object_url"):
            return self.viewset.get_object_url(self.request, obj)
        else:
            if hasattr(obj, "get_absolute_url") and self.has_view_perm(
                self.request.user, obj
            ):
                return obj.get_absolute_url()

    @cached_property
    def list_columns(self):
        return {
            column_name: self.get_column_def(column_name)
            for column_name in self.get_columns()
        }

    def format_value(self, obj, column, value):
        result = column.format_value(obj, value)
        if column.attr_name in self.get_object_link_columns():
            url = self.get_object_url(obj)
            if url:
                result = format_html('<a href="{}">{}</a>', url, result)
        return result

    def get_page_data(self, page):
        """Formated page data for a table.

        Returned data is a list of list of cell values zipped with column definitions.
        [[(column, value), (column, value), ...], ...]
        """
        for obj in page:
            yield obj, [
                (
                    column_def,
                    self.format_value(obj, column_def, column_def.get_value(obj)),
                )
                for column_def in self.list_columns.values()
            ]

    def get_page_actions(self, *actions):
        if self.viewset is not None and hasattr(self.viewset, "get_list_page_actions"):
            actions = self.viewset.get_list_page_actions(self.request) + actions
        if self.page_actions:
            actions = self.page_actions + actions
        return actions

    @viewprop
    def queryset(self):
        if self.viewset is not None and hasattr(self.viewset, "get_queryset"):
            return self.viewset.get_queryset(self.request)
        return None

    def get_template_names(self):
        """
        Return a list of template names to be used for the view.

        If `self.template_name` undefined, uses::
             [<app_label>/<model_label>_list.html,
              'viewflow/views/list.html']
        """
        if self.template_name is None:
            opts = self.model._meta
            return [
                "{}/{}{}.html".format(
                    opts.app_label, opts.model_name, self.template_name_suffix
                ),
                "viewflow/views/list.html",
            ]
        return [self.template_name]

    def dispatch(self, request, *args, **kwargs):
        if not self.has_view_permission(self.request.user):
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name="dispatch")
class ListModelView(
    BulkActionsMixin,
    FilterableViewMixin,
    OrderableListViewMixin,
    SearchableViewMixin,
    BaseListModelView,
):
    """
    Render some list of objects.
    """
