from __future__ import unicode_literals

import django
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.db.models.constants import LOOKUP_SEP


try:
    from django.db.models.query import ModelIterable
except ImportError:
    # Django 1.8
    ModelIterable = object

from .activation import STATUS
from .fields import ClassValueWrapper


def _available_flows(flow_classes, user):
    result = []
    for flow_class in flow_classes:
        opts = flow_class.process_class._meta
        view_perm = "{}.view_{}".format(opts.app_label, opts.model_name)
        if user.has_perm(view_perm):
            result.append(flow_class)
    return result


def _get_related_path(model, base_model):
    """Return path suitable for select related for subclass."""
    ancestry = []

    if model._meta.proxy:
        for parent in model._meta.get_parent_list():
            if not parent._meta.proxy:
                model = parent
                break

    parent = model._meta.get_ancestor_link(base_model)

    while parent is not None:
        related = parent.remote_field if hasattr(parent, 'remote_field') else parent.rel

        ancestry.insert(0, related.get_accessor_name())
        parent_model = related.model

        parent = parent_model._meta.get_ancestor_link(base_model)

    return LOOKUP_SEP.join(ancestry)


def _get_sub_obj(obj, query):
    rel, _, query = query.partition(LOOKUP_SEP)

    try:
        node = getattr(obj, rel)
    except ObjectDoesNotExist:
        return None

    if query:
        return _get_sub_obj(node, query)
    else:
        return node


def coerce_to_related_instance(instance, target_model):
    """Return subclass of the base object."""
    related = _get_related_path(target_model, instance.__class__)
    if related:
        instance = _get_sub_obj(instance, related)
    if instance and not isinstance(instance, target_model):
        # Coerce proxy classes
        instance.__class__ = target_model
    return instance


class ProcessIterable(ModelIterable):
    def __iter__(self):
        base_iterator = super(ProcessIterable, self).__iter__()
        if getattr(self.queryset, '_coerced', False):
            for process in base_iterator:
                if isinstance(process, self.queryset.model):
                    process = coerce_to_related_instance(process, process.flow_class.process_class)
                yield process
        else:
            for process in base_iterator:
                yield process


class ProcessQuerySet(QuerySet):
    """Base manager for the flow Process."""

    def __init__(self, *args, **kwargs):
        super(ProcessQuerySet, self).__init__(*args, **kwargs)
        self._iterable_class = ProcessIterable

    def filter(self, *args, **kwargs):
        """Queryset filter allows to use `flow_class` class values."""
        flow_class = kwargs.pop('flow_class', None)
        if flow_class and not isinstance(flow_class, ClassValueWrapper):
            kwargs['flow_class'] = ClassValueWrapper(flow_class)

        return super(ProcessQuerySet, self).filter(*args, **kwargs)

    def coerce_for(self, flow_classes):
        """Return subclass instances of the Task."""
        self._coerced = True

        flow_classes = list(flow_classes)

        related = filter(
            None, map(
                lambda flow_class: _get_related_path(flow_class.process_class, self.model),
                flow_classes))

        return self.filter(flow_class__in=flow_classes).select_related(*related)

    def filter_available(self, flow_classes, user):
        """List of processes available to view for the user."""
        return self.model.objects.coerce_for(_available_flows(flow_classes, user))

    def _chain(self, **kwargs):
        if hasattr(self, '_coerced'):
            kwargs['_coerced'] = self._coerced

        return super(ProcessQuerySet, self)._chain(**kwargs)

    def _clone(self, *args, **kwargs):
        if django.VERSION >= (2, 0):
            # attr cloning happens in self._chain()
            return super(ProcessQuerySet, self)._clone()

        try:
            kwargs.update({'_coerced': self._coerced})
        except AttributeError:
            pass
        return super(ProcessQuerySet, self)._clone(*args, **kwargs)

    def iterator(self):
        """Coerce queryset results to process subclasses."""

        # django 1.8 only
        base_iterator = super(ProcessQuerySet, self).iterator()
        if getattr(self, '_coerced', False):
            for process in base_iterator:
                if isinstance(process, self.model):
                    process = coerce_to_related_instance(process, process.flow_class.process_class)
                yield process
        else:
            for process in base_iterator:
                yield process


class TaskIterable(ModelIterable):
    def __iter__(self):
        base_iterator = super(TaskIterable, self).__iter__()
        if getattr(self.queryset, '_coerced', False):
            for task in base_iterator:
                if isinstance(task, self.queryset.model):
                    task = coerce_to_related_instance(task, task.flow_task.flow_class.task_class)
                yield task
        else:
            for task in base_iterator:
                yield task


class TaskQuerySet(QuerySet):
    """Base manager for the Task."""

    def __init__(self, *args, **kwargs):
        super(TaskQuerySet, self).__init__(*args, **kwargs)
        self._iterable_class = TaskIterable

    def filter(self, *args, **kwargs):
        """Queryset filter allows to use `process__flow_class` class values."""
        flow_class = kwargs.pop('process__flow_class', None)
        if flow_class and not isinstance(flow_class, ClassValueWrapper):
            kwargs['process__flow_class'] = ClassValueWrapper(flow_class)

        return super(TaskQuerySet, self).filter(*args, **kwargs)

    def coerce_for(self, flow_classes):
        """Return subclass instances of the Task."""
        self._coerced = True
        flow_classes = list(flow_classes)

        related = filter(
            None, map(
                lambda flow_class: _get_related_path(flow_class.task_class, self.model),
                flow_classes))

        return self.filter(process__flow_class__in=flow_classes).select_related('process', *related)

    def user_queue(self, user, flow_class=None):
        """List of tasks of the flow_class permitted for user."""
        queryset = self.filter(flow_task_type='HUMAN')

        if flow_class is not None:
            if not isinstance(flow_class, ClassValueWrapper):
                flow_class = ClassValueWrapper(flow_class)

            queryset = queryset.filter(process__flow_class=flow_class)

        if not user.is_superuser:
            has_permission = Q(owner_permission__in=user.get_all_permissions()) \
                | Q(owner_permission__isnull=True) \
                | Q(owner=user)

            queryset = queryset.filter(has_permission)

        return queryset

    def user_archive(self, user, flow_class=None):
        """List of tasks of the flow_class completed by the user."""
        queryset = self.filter(flow_task_type='HUMAN')

        if flow_class is not None:
            if not isinstance(flow_class, ClassValueWrapper):
                flow_class = ClassValueWrapper(flow_class)

            queryset = queryset.filter(process__flow_class=flow_class)

        return queryset.filter(owner=user, finished__isnull=False)

    def filter_available(self, flow_classes, user):
        """List of tasks available to view for the user."""
        return self.model.objects.coerce_for(_available_flows(flow_classes, user))

    def inbox(self, flow_classes, user):
        """List of tasks assigned to the user."""
        return self.filter_available(flow_classes, user) \
                   .filter(owner=user, status=STATUS.ASSIGNED)

    def queue(self, flow_classes, user):
        """List of tasks permitted to assign for the user."""
        return self.filter_available(flow_classes, user) \
                   .user_queue(user) \
                   .filter(status=STATUS.NEW)

    def archive(self, flow_classes, user):
        """List of tasks finished by the user."""
        return self.filter_available(flow_classes, user) \
            .filter(owner=user, finished__isnull=False)

    def _chain(self, **kwargs):
        if hasattr(self, '_coerced'):
            kwargs['_coerced'] = self._coerced

        return super(TaskQuerySet, self)._chain(**kwargs)

    def _clone(self, *args, **kwargs):
        if django.VERSION >= (2, 0):
            return super(TaskQuerySet, self)._clone()

        try:
            kwargs.update({'_coerced': self._coerced})
        except AttributeError:
            pass
        return super(TaskQuerySet, self)._clone(*args, **kwargs)

    def iterator(self):
        """Coerce queryset results to process subclasses."""
        # django 1.8 only
        base_iterator = super(TaskQuerySet, self).iterator()
        if getattr(self, '_coerced', False):
            for task in base_iterator:
                if isinstance(task, self.model):
                    task = coerce_to_related_instance(task, task.flow_task.flow_class.task_class)
                yield task
        else:
            for task in base_iterator:
                yield task


ProcessManager = ProcessQuerySet.as_manager()
TaskManager = TaskQuerySet.as_manager()
