import django
from django.db import models
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.db.models.constants import LOOKUP_SEP

from .activation import STATUS
from .compat import manager_from_queryset
from .fields import ClassValueWrapper


def _available_flows(flow_classes, user):
    result = []
    for flow_cls in flow_classes:
        opts = flow_cls.process_cls._meta
        view_perm = "{}.view_{}".format(opts.app_label, opts.model_name)
        if user.has_perm(view_perm):
            result.append(flow_cls)
    return result


def _get_related_path(model, base_model):
    """
    Return path suitable for select related for sublcass
    """
    ancestry = []

    if model._meta.proxy:
        for parent in model._meta.get_parent_list():
            if not parent._meta.proxy:
                model = parent
                break

    parent = model._meta.get_ancestor_link(base_model)

    while parent is not None:
        ancestry.insert(0, parent.related.get_accessor_name())

        if django.VERSION < (1, 8):
            parent_model = parent.related.parent_model
        else:
            parent_model = parent.related.model

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


class ProcessQuerySet(QuerySet):
    def filter(self, *args, **kwargs):
        flow_cls = kwargs.pop('flow_cls', None)
        if flow_cls and not isinstance(flow_cls, ClassValueWrapper):
            kwargs['flow_cls'] = ClassValueWrapper(flow_cls)

        return super(ProcessQuerySet, self).filter(*args, **kwargs)

    def coerce_for(self, flow_classes):
        self._coerced = True

        flow_classes = list(flow_classes)

        related = filter(
            None, map(
                lambda flow_cls: _get_related_path(flow_cls.process_cls, self.model),
                flow_classes))

        return self.filter(flow_cls__in=flow_classes).select_related(*related)

    def filter_available(self, flow_classes, user):
        return self.model.objects.coerce_for(_available_flows(flow_classes, user))

    def _clone(self, klass=None, setup=False, **kwargs):
        try:
            kwargs.update({'_coerced': self._coerced})
        except AttributeError:
            pass
        return super(ProcessQuerySet, self)._clone(klass, setup, **kwargs)

    def iterator(self):
        """
        Coerce queryset results to process subclasses depends onf flow_cls.process_cls
        """
        base_itererator = super(ProcessQuerySet, self).iterator()
        if getattr(self, '_coerced', False):
            for process in base_itererator:
                related = _get_related_path(process.flow_cls.process_cls, self.model)
                if related:
                    process = _get_sub_obj(process, related)
                if process and not isinstance(process, process.flow_cls.process_cls):
                    # Cource proxy classes
                    process.__class__ = process.flow_cls.process_cls
                yield process
        else:
            for process in base_itererator:
                yield process


class TaskQuerySet(QuerySet):
    def coerce_for(self, flow_classes):
        self._coerced = True
        flow_classes = list(flow_classes)

        related = filter(
            None, map(
                lambda flow_cls: _get_related_path(flow_cls.task_cls, self.model),
                flow_classes))

        return self.filter(process__flow_cls__in=flow_classes).select_related('process', *related)

    def user_queue(self, user, flow_cls=None):
        """
        List of tasks permitted for user
        """
        queryset = self.filter(flow_task_type='HUMAN')

        if flow_cls is not None:
            queryset = queryset.filter(process__flow_cls=flow_cls)

        if not user.is_superuser:
            has_permission = Q(owner_permission__in=user.get_all_permissions()) \
                | Q(owner_permission__isnull=True) \
                | Q(owner=user)

            queryset = queryset.filter(has_permission)

        return queryset

    def filter_available(self, flow_classes, user):
        return self.model.objects.coerce_for(_available_flows(flow_classes, user))

    def inbox(self, flow_classes, user):
        """
        Tasks for user execution
        """
        return self.filter_available(flow_classes, user) \
                   .filter(owner=user, status=STATUS.ASSIGNED)

    def queue(self, flow_classes, user):
        """
        Unassigned tasks for permitter for the user
        """
        return self.filter_available(flow_classes, user) \
                   .user_queue(user) \
                   .filter(status=STATUS.NEW)

    def archive(self, flow_classes, user):
        """
        Finished by user tasks
        """
        return self.filter_available(flow_classes, user) \
            .filter(owner=user, finished__isnull=False)

    def _clone(self, klass=None, setup=False, **kwargs):
        try:
            kwargs.update({'_coerced': self._coerced})
        except AttributeError:
            pass
        return super(TaskQuerySet, self)._clone(klass, setup, **kwargs)

    def iterator(self):
        """
        Coerce queryset results to process subclasses depends onf flow_cls.task_cls
        """
        base_itererator = super(TaskQuerySet, self).iterator()
        if getattr(self, '_coerced', False):
            for task in base_itererator:
                related = _get_related_path(task.process.flow_cls.task_cls, self.model)
                if related:
                    task = _get_sub_obj(task, related)
                if task and not isinstance(task, task.process.flow_cls.task_cls):
                    # Cource proxy classes
                    task.__class__ = task.process.flow_cls.task_cls
                yield task
        else:
            for task in base_itererator:
                yield task


ProcessManager = manager_from_queryset(models.Manager, ProcessQuerySet)
TaskManager = manager_from_queryset(models.Manager, TaskQuerySet)
