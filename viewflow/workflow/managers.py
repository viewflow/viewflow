from django.db import models
from django.db.models import Q, F, Value
from django.db.models.functions import Concat
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
from django.db.models.constants import LOOKUP_SEP
from django.db.models.query import ModelIterable

from .status import STATUS
from .utils import get_next_process_task


def _available_flows(flow_classes, user):
    result = []
    for flow_class in flow_classes:
        if flow_class.instance.has_view_permission(user):
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
        related = parent.remote_field if hasattr(parent, "remote_field") else parent.rel

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
        base_iterator = super().__iter__()
        if getattr(self.queryset, "_coerced", False):
            for process in base_iterator:
                if isinstance(process, self.queryset.model):
                    process = coerce_to_related_instance(
                        process, process.flow_class.process_class
                    )
                yield process
        else:
            for process in base_iterator:
                yield process


class ProcessQuerySet(QuerySet):
    """Base manager for the flow Process."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._iterable_class = ProcessIterable

    def coerce_for(self, flow_classes):
        """Return subclass instances of the Task."""
        self._coerced = True

        flow_classes = list(flow_classes)

        related = filter(
            None,
            map(
                lambda flow_class: _get_related_path(
                    flow_class.process_class, self.model
                ),
                flow_classes,
            ),
        )

        return self.filter(flow_class__in=flow_classes).select_related(*related)

    def filter_available(self, flow_classes, user):
        """List of processes available to view for the user."""
        return self.model.objects.coerce_for(_available_flows(flow_classes, user))

    def _chain(self, **kwargs):
        chained = super()._chain(**kwargs)
        if hasattr(self, "_coerced"):
            chained._coerced = self._coerced
        return chained


class TaskIterable(ModelIterable):
    def __iter__(self):
        base_iterator = super().__iter__()
        if getattr(self.queryset, "_coerced", False):
            for task in base_iterator:
                if isinstance(task, self.queryset.model):
                    task = coerce_to_related_instance(
                        task, task.flow_task.flow_class.task_class
                    )
                yield task
        else:
            for task in base_iterator:
                yield task


class TaskQuerySet(QuerySet):
    """Base manager for the Task."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._iterable_class = TaskIterable

    def coerce_for(self, flow_classes):
        """Return subclass instances of the Task."""
        self._coerced = True
        flow_classes = list(flow_classes)

        related = filter(
            None,
            map(
                lambda flow_class: _get_related_path(flow_class.task_class, self.model),
                flow_classes,
            ),
        )

        return self.filter(process__flow_class__in=flow_classes).select_related(
            "process", *related
        )

    def user_queue(self, user, flow_class=None):
        """List of tasks of the flow_class permitted for user."""
        queryset = self.filter(flow_task_type="HUMAN")

        if flow_class is not None:
            queryset = queryset.filter(process__flow_class=flow_class)

        if not user.is_superuser:
            has_permission = Q(owner_permission__isnull=True) | Q(owner=user)

            if "guardian" in settings.INSTALLED_APPS:
                from guardian.models import UserObjectPermission, GroupObjectPermission

                queryset = queryset.annotate(
                    owner_permission_obj_check=Concat(
                        F("owner_permission"),
                        Value("_"),
                        F("owner_permission_obj_pk"),
                        output_field=models.CharField(),
                    )
                )

                all_user_perms = user.get_all_permissions()
                if hasattr(user, "_viewflow_per_object_perm_cache"):
                    per_object_perms = user._viewflow_per_object_perm_cache
                else:
                    per_object_perms = {
                        "{}.{}_{}".format(
                            userperm.content_type.app_label,
                            userperm.permission.codename,
                            userperm.object_pk,
                        )
                        for userperm in UserObjectPermission.objects.filter(user=user)
                    }

                    per_object_perms = per_object_perms | {
                        "{}.{}_{}".format(
                            groupperm.content_type.app_label,
                            groupperm.permission.codename,
                            groupperm.object_pk,
                        )
                        for groupperm in GroupObjectPermission.objects.filter(
                            group__in=user.groups.all()
                        )
                    }
                    user._viewflow_per_object_perm_cache = per_object_perms

                has_permission = (
                    has_permission
                    | Q(owner_permission__in=all_user_perms)
                    | Q(owner_permission_obj_check__in=per_object_perms)
                )
            else:
                has_permission = (
                    Q(owner_permission__in=user.get_all_permissions()) | has_permission
                )

            queryset = queryset.filter(has_permission)

        return queryset

    def user_archive(self, user, flow_class=None):
        """List of tasks of the flow_class completed by the user."""
        queryset = self.filter(flow_task_type="HUMAN")

        if flow_class is not None:
            queryset = queryset.filter(process__flow_class=flow_class)

        return queryset.filter(owner=user, finished__isnull=False)

    def filter_available(self, flow_classes, user):
        """List of tasks available to view for the user."""
        return self.model.objects.coerce_for(_available_flows(flow_classes, user))

    def inbox(self, flow_classes, user):
        """List of tasks assigned to the user."""
        return self.filter_available(flow_classes, user).filter(
            owner=user, status=STATUS.ASSIGNED
        )

    def queue(self, flow_classes, user):
        """List of tasks permitted to assign for the user."""
        return (
            self.filter_available(flow_classes, user)
            .user_queue(user)
            .filter(status=STATUS.NEW)
        )

    def archive(self, flow_classes, user):
        """List of tasks finished by the user."""
        return self.filter_available(flow_classes, user).filter(
            owner=user, finished__isnull=False
        )

    def next_user_task(self, process, user):
        """
        Lookup for the next task for a user execution.

        Prefer assigned tasks first, if not, return first task from user queue
        """

        # task inside a same process
        task = get_next_process_task(self, process, user)

        # task inside subprocess
        if task is None:
            subprocess_task = self.filter(process__parent_task__process=process).first()
            if subprocess_task:
                task = get_next_process_task(self, subprocess_task.process, user)

        # task inside parent process
        if task is None and process.parent_task_id:
            task = get_next_process_task(self, process.parent_task.process, user)

        # task inside other subprocesses of parent task
        if task is None and process.parent_task_id:
            processes = process.__class__._default_manager.filter(
                parent_task__process=process.parent_task.process
            ).exclude(pk=process.pk)
            for sub_process in processes:
                task = get_next_process_task(self, sub_process, user)
                if task:
                    break

        return task

    def _chain(self, **kwargs):
        chained = super()._chain(**kwargs)
        if hasattr(self, "_coerced"):
            chained._coerced = self._coerced
        return chained
